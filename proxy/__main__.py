import sys
import getopt
import logging
from logging import info, error

from proxy import flask_server

def print_usage():
    print("USAGE\n\tpython3 proxy [OPTIONS]\n")
    print("OPTIONS\n\t--flaskserver <master_hostname>\tStarts the flask server, connecting to the master specified\n")


def print_usage_and_exit():
    print_usage()
    exit(1)


def main():
    print(f"Running main({sys.argv})...")

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "mwfp:u:l", ["flaskserver", "port=", "master_uri=", "local"])

        node_type_arg = None
        port_arg = None
        master_uri_arg = None
        local_testing = False

        for opt, arg in opts:
            if opt in ['-f', '--flaskserver']:
                node_type_arg = "flaskserver"
            elif opt in ['--master_uri']:
                master_uri_arg = arg
            elif opt in ['-p', '--port']:
                port_arg = int(arg)
            elif opt in ['-l', '--local']:
                local_testing = True

        if node_type_arg == "flaskserver":
            ok, master_hostname, master_port = is_valid_master_uri(master_uri_arg)
            if ok:
                if port_arg is not None:
                    flask_server.run(master_hostname, master_port, port_arg)
                else:
                    flask_server.run(master_hostname, master_port)
            else:
                flask_server.run()

    except Exception as e:
        print(f"Error: {e}")
        print_usage_and_exit()


def is_valid_master_uri(uri):
    print(f"uri: {uri}")
    if uri is not None and uri != "":
        if ":" in uri:
            print("uri has :")
            parts = uri.split(":")
            if len(parts) == 2:
                hostname = parts[0]
                try:
                    port = int(parts[1])
                    return True, hostname, port
                except ValueError as e:
                    error(f"Unable to parse port number: {e}")
    return False, uri, 8080


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname) - 4s %(message)s',
                        level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')
    main()
