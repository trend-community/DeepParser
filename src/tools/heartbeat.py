import configparser, logging, os, requests, time


current_milli_time = lambda: int(round(time.time() * 1000))


if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    Config = configparser.ConfigParser()
    Config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'heartbeat.ini'))

    servers = [x.strip() for x in Config.get("main", "servers").splitlines() if x]
    #print(str(servers))
    extra = '/LexicalAnalyze?Sentence=%22ab%20cd%22'
    for i in  range(len(servers)):
        starttime = current_milli_time()
        try:
            logging.debug("start:")
            ret = requests.get(servers[i] + extra)
            if 100 < ret.status_code < 400:
                logging.info("[SERVER " + servers[i] + "][TIME] " + str(current_milli_time() - starttime) )
            else:
                logging.error("[SERVER " + servers[i] + "][TIME] " + str(current_milli_time() - starttime) + "\tresponse code:" + ret.status_code)

        except Exception as e:
            logging.error("[SERVER " + servers[i] + "][TIME] " + str(current_milli_time() - starttime) + "\tException:" + str(e))







