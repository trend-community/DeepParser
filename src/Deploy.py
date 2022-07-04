### The task of this program is to create deploy package:

# 1, copy the spedified .ini file into config.ini
# 2, check the pipeline setting from the config.ini:
# 3.1 confirm the dump folder is complete
# 4, delete rule files and lexicon files from the pipeline folder
# 5, delete all other fsa folders.
# 6, compile the .py files into .pyc
# 7, delete .py files

import logging, argparse,  os, shutil, configparser


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("configfile", help="Sample: config.X-law.ini")
    args = parser.parse_args()

    configfilelocation = os.path.join(os.path.dirname(__file__), args.configfile)
    if not os.path.exists(configfilelocation):
        logging.error("The specified config file {} doesn't exist.".format(configfilelocation))
        exit(1)

    #shutil.copyfile(args.configfile, "config.ini")
    ParserConfig = configparser.ConfigParser()
    ParserConfig.read(os.path.join(configfilelocation))

    pipelinefilelocation = os.path.join(os.path.dirname(__file__), ParserConfig.get("main", "Pipelinefile"))
    if not os.path.exists(pipelinefilelocation):
        logging.error("The specified pipeline file {} doesn't exist.".format(pipelinefilelocation))
        exit(1)

    pipelinefolder = os.path.dirname(pipelinefilelocation)
    pipelinedumpfolder = os.path.join(pipelinefolder, "dump")
    if not os.path.exists(pipelinedumpfolder):
        logging.error("The dump folder {} doesn't exist. ".format(pipelinedumpfolder))
        exit(1)     # don't process.

    LoadFrom = ParserConfig.get("main", "loadfrom").lower()
    if LoadFrom != "dump":
        logging.error("In {}, please modify the LoadFrom to 'dump' before deployment ".format(configfilelocation))
        exit(1)  # don't process.

    RunType = ParserConfig.get("main", "loadfrom").lower()
    if LoadFrom == "debug":
        logging.error("In {}, please modify the RunType to 'Release' or 'Release_Analyze' before deployment ".format(configfilelocation))
        exit(1)  # don't process.

    logging.info("There are {} files in the dump folder".format(len([name for name in os.listdir(pipelinedumpfolder)]) - 2))

    # Start removing files that are not "feature*" in the pipeline folder
    for pipelinefile in os.listdir(pipelinefolder):
        if os.path.isdir(os.path.join(pipelinefolder, pipelinefile)):
            continue
        if pipelinefile.startswith("feature"):
            continue
        os.remove(os.path.join(pipelinefolder, pipelinefile))

    # need to remove all other folder in fsa
    pipelinename = os.path.basename(pipelinefolder)
    for pipeline in os.listdir(os.path.join(pipelinefolder, "..")):
        if pipeline in [pipelinename, 'ontology']:
            continue
        shutil.rmtree(os.path.join(pipelinefolder, "..", pipeline))

    import utils
    utils.runSimpleSubprocess("python3 -m compileall -b " + os.path.dirname(__file__))
    utils.runSimpleSubprocess("rm {}/*.py".format(os.path.dirname(os.path.realpath(__file__))))

    shutil.copyfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), args.configfile),
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.ini"))
    shutil.copyfile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "assets", "parser.empty.db"),
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "assets", "parser.db"))
