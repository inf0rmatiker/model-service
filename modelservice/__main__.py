import os
import sys
import getopt
import logging
from logging import error

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from modelservice import master
from modelservice import proxy


def print_usage():
    print("USAGE\n\tpython3.8 modelservice [OPTIONS]\n")
    print("OPTIONS\n\t--master <master_port>\t\tStarts the master server")
    print("\tExample: python3.8 modelservice --master 50051\n")
    print("OPTIONS\n\t--proxy <master_hostname>\tStarts the Flask server, connecting to the master specified\n")
    print("\tExample: python3.8 modelservice --flaskserver lattice-150:50051 5000\n")


def print_usage_and_exit():
    print_usage()
    exit(1)


def main():
    print(f"Running main({sys.argv})...")

    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "mwfp:u:", ["proxy", "port=", "master_uri="])

        node_type_arg = None
        port_arg = None
        master_uri_arg = None

        for opt, arg in opts:
            if opt in ['-m', '--master']:
                node_type_arg = "master"
            elif opt in ['-f', '--proxy']:
                node_type_arg = "flaskserver"
            elif opt in ['--master_uri']:
                master_uri_arg = arg
            elif opt in ['-p', '--port']:
                port_arg = int(arg)

        if node_type_arg == "master":
            master.run(master_port=port_arg) if port_arg is not None else master.run()

        if node_type_arg == "flaskserver":
            ok, master_hostname, master_port = is_valid_master_uri(master_uri_arg)
            if ok:
                if port_arg is not None:
                    proxy.run(master_hostname, master_port, port_arg)
                else:
                    proxy.run(master_hostname, master_port)
            else:
                proxy.run()

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
