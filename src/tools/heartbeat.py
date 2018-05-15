import configparser, logging, os, requests, time


current_milli_time = lambda: int(round(time.time() * 1000))


if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    Config = configparser.ConfigParser()
    Config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'heartbeat.ini'))

    servers = [x.strip() for x in Config.get("main", "servers").splitlines() if x]
    print(str(servers))
    extra = '?Sentence=%22ab%20cd%22'
    for i in  range(len(servers)):
        starttime = current_milli_time()
        try:
            ret = requests.get(servers[i] + extra)
            logging.info("[SERVER " + str(i) + "][TIME] " + str(current_milli_time() - starttime))
        except Exception as e:
            logging.error("[SERVER " + str(i) + "][TIME] " + str(current_milli_time() - starttime))







