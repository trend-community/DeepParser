import configparser, logging, os, requests, time


current_milli_time = lambda: int(round(time.time() * 1000))

def HBTask(server):
    link_extra = Config.get("main", "link_extra")
    starttime = current_milli_time()

    try:
        logging.debug("start:" + link_extra)
        ret = requests.get(server + link_extra)
        if 100 < ret.status_code < 400:
            return("[SERVER " + server + "][TIME] " + str(
                current_milli_time() - starttime))
        else:
            return("[SERVER " + server + "][TIME] " + str(
                current_milli_time() - starttime) + "\tresponse code:" + ret.status_code)

    except Exception as e:
        return(  "[SERVER " + server + "][TIME] " + str(
            current_milli_time() - starttime) + "\tException:" + str(e))


if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    Config = configparser.RawConfigParser()
    Config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'heartbeat.ini'))

    servers = [x.strip() for x in Config.get("main", "servers").splitlines() if x]
    #print(str(servers))
    # for i in  range(len(servers)):
    #     HBTask(servers[i])
    #serials

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        Result = {}
        # We can use a with statement to ensure threads are cleaned up promptly
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(HBTask, server): server for server in servers}
        future_new = {}
        logging.info("There are " + str(len(future_to_url)) + " to process.")
        for future in concurrent.futures.as_completed(future_to_url):
            s = future_to_url[future]
            try:
                Result[s] = future.result()
            except Exception as exc:
                logging.debug('%r generated an exception: \n %s' % (s, exc))

        logging.info("Done of retrieving data")

    for server in servers:
        if server in Result:
            print(server + '\t' + Result[server] )
        else:
            print("Failed: " + server )