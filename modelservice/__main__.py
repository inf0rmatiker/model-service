import os
import sys
import getopt
import logging
from logging import error

from modelservice import master
from modelservice import proxy
from modelservice import worker

def print_usage():
    print("USAGE\n\tpython3.8 modelservice [OPTIONS]\n")
    print("OPTIONS\n\t--master <master_port>\t\t\tStarts the master server")
    print("\tExample: python3.8 modelservice --master 50051\n")
    print("\t--proxy <master_uri> <proxy_port>\tStarts the Flask server (proxy), connecting to the master specified")
    print("\tExample: python3.8 modelservice --proxy antlion:50051 5000\n")
    print("\t--worker <master_uri> <worker_port>\tStarts the Worker server, connecting to the master specified")
    print("\tExample: python3.8 modelservice --worker antlion:50051 50055\n")


def print_usage_and_exit():
    print_usage()
    exit(1)


def main():
    print(f"Running main({sys.argv})...")

    argv = sys.argv[1:]
    try:

        opts, args = getopt.getopt(argv, "mwfp:u:", ["master", "worker", "proxy", "port=", "master_uri="])

        node_type_arg = None
        port_arg = None
        master_uri_arg = None

        for opt, arg in opts:
            if opt in ['-m', '--master']:
                node_type_arg = "master"
            elif opt in ['-f', '--proxy']:
                node_type_arg = "proxy"
            elif opt in ['-w', '--worker']:
                node_type_arg = "worker"
            elif opt in ['--master_uri']:
                master_uri_arg = arg
            elif opt in ['-p', '--port']:
                port_arg = int(arg)

        if node_type_arg == "master":
            master.run(master_port=port_arg) if port_arg is not None else master.run()

        elif node_type_arg == "proxy":
            ok, master_hostname, master_port = is_valid_master_uri(master_uri_arg)
            if ok:
                if port_arg is not None:
                    proxy.run(master_hostname, master_port, port_arg)
                else:
                    proxy.run(master_hostname, master_port)
            else:
                proxy.run()

        elif node_type_arg == "worker":
            ok, master_hostname, master_port = is_valid_master_uri(master_uri_arg)
            if ok:
                if port_arg is not None:
                    worker.run(master_hostname, master_port, port_arg)
                else:
                    worker.run(master_hostname, master_port)
            else:
                worker.run()

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
