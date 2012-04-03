import sys
import getopt
import urllib
import httplib
import re
from copy import deepcopy


class CoalitionControl(object):
    default_options = dict(dir='.', title='New job', startIndex=1, endIndex=1,
            retry=10, affinity='', priority=1000, timeout=0, parent=0,
            dependencies='', id=-1, localprogress=None, globalprogress=None,)

    def __init__(self, server_url):
        clean_url = re.sub(r'^http://', '', server_url)
        clean_url = re.sub(r'/*$', '', clean_url)
        self.server_url = clean_url

    def add(self, command, **kwargs):
        '''
        Submit a new job to the coalition server at server_url.

        For example, assuming a coalition server is running at
        http://localhost:19211, the following will submit a job to run the 'date'
        command:

        >>> job_id = add('http://localhost:19211/', 'date', priority=2000, title='Date test')
        >>> job_id is None
        False
        '''
        options = deepcopy(self.default_options)
        options.update(kwargs)
        options.update({'cmd': command})
        for attr in ['localprogress', 'globalprogress']:
            if options.get(attr, True) is None:
                # global/localprogress was specified as None, so delete it
                del options[attr]
        params = urllib.urlencode(options)
        conn = httplib.HTTPConnection(self.server_url)
        conn.request('GET', '/json/addjob?' + params)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return data

    def get_jobs(self, parent=0):
        params = urllib.urlencode({'id': parent, 'parent': parent})
        conn = httplib.HTTPConnection(self.server_url)
        conn.request("GET", "/json/getjobs?" + params)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        data = re.sub(r',null', r',None', data)

        data = eval(data)

        vars = data["Vars"]
        jobs = data["Jobs"]
        parents = data["Parents"]
        return parents, [dict(zip(vars, j)) for j in jobs]

    def list(self, parent=0):
        parents, jobs = self.get_jobs(parent)
        
        parents_info=''
        for i in range(len(parents)):
            parents_info = parents_info+ str(parents[i]["ID"])+" " +str(parents[i]["Title"])+ " > "
        print(parents_info)
        for i in range(len(jobs)):
            print jobs[i]

    def remove(self, id):
        if id < 0: 
            print("Use option -i to specify the job id to remove")
        else:
            params = urllib.urlencode({'id':id})
            conn = httplib.HTTPConnection(self.server_url)
            conn.request("GET", "/json/clearjobs?" + params)
            response = conn.getresponse()
            data = response.read()
            conn.close()



def _parse_args(argv):
    """Parses arguments, returns ``(options, args)``."""
    from argparse import ArgumentParser

    parser = ArgumentParser(description="""\
Control the Coalition server located at SERVER_URL.""",
                            epilog="""\
(C) 2012  Christian Fobel, licensed under the terms of GPL3.""",)
    parser.add_argument('-d', '--directory', dest='dir',
            help='Working directory (default: %(default)s)')
    parser.add_argument('-t', '--title',
            help='Set the job title (default: %(default)s)')
    parser.add_argument('-p', '--priority',
            help='Priority of the job (default: %(default)s)')
    parser.add_argument('-r', '--retry',
            help='Number of retry this jobs can do (default: %(default)s)')
    parser.add_argument('-a', '--affinity',
            help='Affinity words to workers, separated by a comma '\
                    '(default: %(default)s)')
    parser.add_argument('-T', '--timeout',
            help='timeout for the job')
    parser.add_argument('-D', '--dependencies',
            help='IDs of the dependent jobs (example : "21 22 23")')
    parser.add_argument('-P', '--parent',
            type=int,
            help='Id of of the parent of the job (default: %(default)s)')
    parser.add_argument('--globalprogress', help='The job progression pattern')
    parser.add_argument('--localprogress',
            help='The second job progression pattern')
    parser.add_argument(nargs=1,
            dest='server_url', default='http://localhost:19211',
            help='Server URL (default: %(default)s)')

    subparsers = parser.add_subparsers(help='Action to perform')
    list_parser = subparsers.add_parser('list',
            help='list the jobs on the server')
    list_parser.set_defaults(action='list')
    add_parser = subparsers.add_parser('add',
            help='add a job, use option -c for command')
    add_parser.add_argument('-c', '--cmd', help='Command to add', required=True)
    add_parser.set_defaults(action='add')
    remove_parser = subparsers.add_parser('remove',
            help='remove job designated by id') 
    remove_parser.add_argument('-i', '--jobid', dest='id', required=True,
            help='ID of the Job')
    remove_parser.set_defaults(action='remove')
    parser.set_defaults(**CoalitionControl.default_options)
    args = parser.parse_args(argv)

    args.server_url = args.server_url[0]

    return args


if __name__ == '__main__':
    args = _parse_args(sys.argv[1:])
    control = CoalitionControl(args.server_url)

    if args.action == 'list':
        control.list(args.parent)
    elif args.action == 'remove':
        control.remove(args.id)
    elif args.action == 'add':
        # not included: args.id
        # startIndex=args.startIndex, endIndex=args.endIndex,
        control.add(args.cmd, dir=args.dir, title=args.title,
            retry=args.retry, affinity=args.affinity, priority=args.priority,
            timeout=args.timeout, parent=args.parent,
            dependencies=args.dependencies, localprogress=args.localprogress,
            globalprogress=args.globalprogress)
