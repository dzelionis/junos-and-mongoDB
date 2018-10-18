#!/usr/bin/python2.7

from jnpr.junos import Device
import jnpr.junos.exception
import jnpr.junos.factory as FactoryLoader

from jnpr.junos.op.arp import ArpTable
from jnpr.junos.op.ccc import CCCTable
from jnpr.junos.op.isis import IsisAdjacencyTable
from jnpr.junos.op.lacp import LacpPortTable
from jnpr.junos.op.routes import RouteTable

from xmljson import badgerfish as bf
from xmljson import parker, Parker
from xml.etree.ElementTree import fromstring
from jnpr.junos.utils.config import Config
import logging as log
from pprint import pprint
from lxml import etree
from pymongo import MongoClient
from bson.json_util import dumps, loads
import yaml,sys,json,datetime
#from json import dumps


LOG_LEVEL='ERROR'
#LOG_LEVEL='INFO'


PATH_TO_YAML='junos_yaml/'  ### PATH to yaml files

## If node list is not defined in arguments, lets use LAB node list...
labNodeList = \
[   "lab.magna.radio.ex4300",
    "lab.magna.radio.sw",
    "lab.magna.core.vc",
    "lab.magna.test.sw",
    "lab.magna.access.srx210",
    "lab.magna.core.acx",
    "lab.magna.core.mx5"]


DATABASE = "test3"      ## Mongo Database Name:
RunAsDeamond = False    ## no output on screen...
NetConfTest  = False    ## Do not write any changes to DB, only test netconf...
LoadFromFile = False    ## Load node list from file....
NodeListFile = ""

# Setting up global vars....
SCRIPT_NAME=sys.argv[0]
jfacts = dict()
nodeList = list()


# Mappings
yamlTBL_to_MongoCollections = {
#  Defining yaml file which contains Junos Pyez Tables
# 'Defining Junos Pyez Table name' : 'mongoDB collection name'


'fpc'           : {
            'FpcHwTBL'                  : 'jnp_fpcHW',
            'FpcMiReHwTBL'              : 'jnp_fpcMiReHW',
            'FpcInfoTBL'                : 'jnp_fpcInfo',
            'FpcMiReInfoTBL'            : 'jnp_fpcMiReInfo',
    },
'inventory'     : { 'ModuleTBL'         :  'jnp_chassisInv'  },
'xcvr'          : { 'XcvrTBL'           :  'jnp_xcvr'        },
'mac-table'     : { 'MacTBL'            :  'jnp_macTable'    },
'vlan'          : { 'VlanDetailTable'   :  'jnp_vlans'       },
'interface'     : {
            'InterfaceTBL'              :  'jnp_interface',
            'InterfaceDescriptionTBL'   :  'jnp_intDesc',
            'InterfaceMediaTBL'         :  'jnp_intMedia',
            'InterfaceExtensiveTBL'     :  'jnp_intExtensive',
    },
'lacp'          : { 'LacpPortTBL'       :  'jnp_lacpPort'     },
'l2vpn'         : {'L2VPNConnectionTBL' :  'jnp_l2vpn'        },
'ccc'           : {'CCCTbl'             :  'jnp_cccInfo'      },
'arp'           : {'ArpTbl'             :  'jnp_arpTable'     },
'isis'          : {'IsisAdjTbl'         :  'jnp_isisAdjacency'},
'rsvp_mpls'     : {
            'MplsLspTBL'                :  'jnp_mplsLsp',
            'RsvpNeighborTBL'           :  'jnp_rsvpNeighbor',
            'RsvpInterfaceTBL'          :  'jnp_rsvpInterface',
            'RsvpSessionTBL'            :  'jnp_rsvpSession',
    },
'lldp'          : {
            'LLDPNeighborTable'         :  'jnp_lldpNeighbors',
            'lldpLocalInfoTable'             :  'jnp_lldpLocalInfo',
            'lldpExportedVlanTable'     :  'jnp_lldpDetail'
    }
}

#If there is any related tables which has to iterate...
yamlTBL_to_MongoCollections_if_related = {
'LLDPNeighborTable'
                : {'lldpInterfaceTable'  :  'jnp_lldpInterface'},
}

colLB = '\033[01;36m'
colCls = '\033[0m'
colBgGr = '\x1b[1;30;42m'
colBgCls = '\x1b[0m'
colPur = '\033[95m'

# ANSI color codes
clr = {
    'RS'    :   "\033[0m",
    'HC'    :   "\033[1m",
    'UL'    :   "\033[4m",
    'INV'   :   "\033[7m",
    'FBLK'  :   "\033[30m",
    'FRED'  :   "\033[31m",
    'FGRN'  :   "\033[32m",
    'FYEL'  :   "\033[33m"
}
FBLE="\\033[34m" # foreground blue
FMAG="\\033[35m" # foreground magenta
FCYN="\\033[36m" # foreground cyan
FWHT="\\033[37m" # foreground white
BBLK="\\033[40m" # background black
BRED="\\033[41m" # background red
BGRN="\\033[42m" # background green
BYEL="\\033[43m" # background yellow
BBLE="\\033[44m" # background blue
BMAG="\\033[45m" # background magenta
BCYN="\\033[46m" # background cyan
BWHT="\\033[47m" # background white



### ------------------------------------------------------------------------------------------
###  Checking for arguments....Printing help....
###                                                 <mod by domas.zelionis@enet.ie>
### -------------------------------------------------------------------------------------------

def showHelpAndExit():
    # Print help and exit....
    print "\n" + colLB + "Juniper to MongoDB Mapper (using NetConf)....\n" + colCls
    print colPur + SCRIPT_NAME + colCls + " [options] [<node_name>...<node_name>..........]"
    print "Options: -d run as deamond...(no output to screen)"
    print "\t -l=<log level>, possible values: [INFO, WARNING, ERROR, CRITICAL]"
    print "\t -t just test NetConf, do not write to DB..."
    print "\t -f path/to/node.list [file structure {<ip><space><name>} per line]"
    exit()

## function for loading node list from a file....

def loadNodeList(FILE, nodeList=list()):

    linesList = list()
    # nodes_tmp = []
    try:
        with open(FILE) as f:
            # Blank lines are not processed
            for lines in f:
                linesList.append(filter(None, (lines.rstrip())))
    except IOError as err:
        print "Error: cant find node list file...exiting..."
        exit()
        log.error('error: failed to load: ' + file + '...' + repr(err) + '. Skipping...')
    else:
        tmpVar = dict()
        for i in range(0, len(linesList) - 1):
            tempVar = {linesList[i].split()[0] : linesList[i].split()[1] }
            nodeList.append(tempVar)
        return nodeList


## Parsing arguments/options
argPos=1
if len(sys.argv) > 1:
    argPos=1
    for i in range(1, len(sys.argv)):
        optFlag = sys.argv[i]
        # if following print help and exit!
        if optFlag == '-h' or optFlag == '-help' or optFlag == '/?' or optFlag == '/h':
            showHelpAndExit()
        elif optFlag == '-l=INFO':
            LOG_LEVEL = 'INFO'
            argPos = argPos + 1
        elif optFlag == '-l=WARNING':
            LOG_LEVEL = 'WARNING'
            argPos = argPos + 1
        elif optFlag == '-l=ERROR':
            LOG_LEVEL = 'ERROR'
            argPos = argPos + 1
        elif optFlag == '-l=CRITICAL':
            LOG_LEVEL = 'CRITICAL'
            argPos = argPos + 1
        elif optFlag == '-d':
            RunAsDeamond == True
            argPos = argPos + 1
        elif optFlag == '-t':
            NetConfTest == True
            argPos = argPos + 1
        elif optFlag == '-f':
            LoadFromFile=True
            NodeListFile=sys.argv[i+1]
            i = i + 1
            argPos = argPos + 2


## Cheking for nodes as arguments or
## definition of node list file

#if len(sys.argv) == argPos and LoadFromFile == False:
#    showHelpAndExit()   ##no nodes defined...

if len(sys.argv) > argPos:
    nodeList = list()
    for i in range(1,len(sys.argv)):
        nodeList.append(sys.argv[i])
    if LoadFromFile == True:
        nodeList = (NodeListFile, nodeList)
elif len(sys.argv) == argPos and LoadFromFile == True:
    nodeList = list()
    nodeList = loadNodeList(NodeListFile, nodeList)
print nodeList

if len(nodeList) == 0:
    nodeList = labNodeList
    print "\n\n " + clr['FYEL'] + "No nodes or node lists is defined as argument,/nusing LAB node list:" + colCls + "\n\t"
    print nodeList
else:
    print "\n" + colLB + "Sucessfully loaded node list:" + colCls
    print nodeList
print "\n"


### ------------------------------------------------------------------------------------------
###                FIRST OF ALL....LOGGING!!!
###                                             <mod by domas.zelionis@enet.ie>
### -------------------------------------------------------------------------------------------


timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
log.basicConfig(filename="net_to_db.log", format='%(asctime)s - %(levelname)s - %(message)s', level=getattr(log, LOG_LEVEL))
console = log.StreamHandler()
console.setLevel(getattr(log, LOG_LEVEL))
formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
log.getLogger('').addHandler(console)



for fileName in yamlTBL_to_MongoCollections:
    # Adding path and '.yml' extension
    file = PATH_TO_YAML + fileName + '.yml'
    try:
        globals().update(FactoryLoader.loadyaml(file))
    except IOError as err:
        log.error('error: failed to load: ' + file + '...' + repr(err) + '. Skipping...')
        continue
    else:
        log.info('Succesfully loaded: ' + file + '...')


# trying to connect to MongoDB using mongo Driver
try:
    dbclient = MongoClient('localhost', 27017)
except pymongo.errors.ServerSelectionTimeoutError as err:
    log.critical("ERROR: failed to connect to DB (" + repr(err) + ")")
    log.critical("ERROR: Exiting....")
    exit(1)

db = getattr(dbclient, DATABASE)
log.info("Connected to MongoDB, using database: " + DATABASE + "...")



def update_data(dev, table, collection, options=''):
    global jfacts

    try:
        tempFunct = globals()[table]
    except KeyError as err:
        print('error: ' + repr(err))
    tempTable = tempFunct(dev)
    try:
        if isinstance(options, str):
            tempTable.get()
        elif isinstance(options, dict):
            tempTable.get(options['get'])
    except jnpr.junos.exception.RpcError as err:
        print('error: ' + repr(err))
        return list()

    jstr = tempTable.to_json()
    jout = json.loads(jstr)

    jout_list = list()
    key_list = list()

    #print jout.keys
    #print key_list
    #for key in jout.keys:
    #    print key
    for item in jout:
        # Adding additional fields per document
        jout[item]['node_name'] = jfacts['node_name']
        jout[item]['node_id'] = jfacts['node_doc_id']
        # removing key to get vlan data on the root level and adding it to the list.
        jout_list.append(jout[item])
        #print jout[item].value
        #key_list.append(item.keys)

    if len(jout_list) != 0:
        dbCollection = getattr(db, collection)
        if isinstance(options, dict):
            if options['db_key'] and options['db_val']:
                dbCollection.remove({'node_name': jfacts['node_name'], options['db_key']: options['db_val']})
            else:
                dbCollection.remove({'node_name': jfacts['node_name']})
        else:
            dbCollection.remove({'node_name': jfacts['node_name']})
        print dbCollection.insert(jout_list)
    #print len(jout)
    #pprint(jout)
    return jout



def update_config(dev, collection):
    global jfacts

    ## RPC call to get node configuration in XML format
    try:
        cnf = dev.rpc.get_config(normalize=True)
    except jnpr.junos.exception.RpcError as err:
        log.error('error: Failed to get a CONFIG copy from device: ' + jfacts['node_name']  + '...' + repr(err) + '. Skipping....')
        return False

    ## cnf = dev.rpc.get_config(filter_xml=etree.XML('<configuration><interfaces/></configuration>'))
    ## Convert XML object into string
    ## cnf = False

    if not isinstance(cnf, bool):
        cfg_str = etree.tostring(cnf)
    else:
        cnf = dev.cli("show configuration | no-more | display xml", warning=False)
        pprint(cnf)
        cfg_str = etree.tostring(cnf)
    result = dumps(parker.data(fromstring(cfg_str), preserve_root=True))

    tmp = list()
    # Remove "." from key values
    result = result.replace("802.3ad", "802_3ad")
    result = result.replace("-802.1", "-802_1")
    ## after normalization empty values was replaced with null, replacing null with True to make it more human readable
    #result = result.replace("null", '"true"')
    result = result.replace("null", "true")

    ## Convert JSON string into JSON object
    jout = dict()
    jout = json.loads(result)
    ## Shift all the data in 'configuration' to the root level.

    for key in jout.keys():
        if key == 'configuration':
            jout = jout['configuration']
    ## Add node_name & node_doc_id to a document
    jout['node_name'] = jfacts['node_name']
    jout['node_id'] = jfacts['node_doc_id']

    #pprint(jout['logical-systems']['name'])
    if len(jout) != 0:
        dbCollection = getattr(db, collection)
        dbCollection.remove({'node_name': jfacts['node_name']})

        ## Pulling configuration from devices and pushing it to 'config' collection (one document per node)
        configuration_doc_id = dbCollection.insert_one(jout).inserted_id

    lSystem = False
    for key in jout.keys():
        if key == 'logical-systems':
            lSystem = True
            break
    if lSystem == True:
        #print len(jout['logical-systems'])
        if len(jout['logical-systems']) != 0:
            tmpList = list()
            for li in range(0, len(jout['logical-systems'])):
                tmpList.append(jout['logical-systems'][li]['name'])

            jfacts['logical-systems'] = tmpList
         #   pprint(jfacts['logical-systems'])
            return 'logical-systems'
    else:
        return True



for node in nodeList:
  jfacts = dict()  ## Cleaning up....

  log.info("NETCONF: connecting to: " + node + "....")
  dev = Device(host=node, user='airspeed', password='', gather_facts=True)
  try:
    dev.open()
  except jnpr.junos.exception.ConnectError as err:
    log.error('error: Failed to connect to: ' + node + '....' + repr(err) + '. Skipping....')
    continue
  else:
    log.info("Collecting facts about device....")
    facts = dev.facts       ## Collecting facts about device
    jfactsStr = dumps(facts)        ## JSON conversions
    jfacts = loads(jfactsStr)

    jfacts['node_name'] = node      ## Adding 'node_name' to facts

    dbDocCount = db.nodes.find({'node_name': node}, {'_id': 1}).count()
    if dbDocCount >= 2:  # To many documents for a node, should be 1, removing all.
        nodeExistsInDb = True
        db.nodes.remove({'node_name': node})
    elif dbDocCount == 1:  # Lets keep same _id
        nodeExistsInDb = True
        jfacts['_id'] = db.nodes.find_one({'node_name': node}, {'_id': 1})['_id']
        db.nodes.remove({'_id': jfacts['_id']})

    # Pushing  facts into 'nodes' collection, one document per node
    jfacts['node_doc_id'] = db.nodes.insert_one(jfacts).inserted_id
    node_doc_id = jfacts['node_doc_id'] # temp var ... should be gone soon...

    if jfacts['model'] == "ACX1100" or jfacts['model'] == "MX5-T":
        log.info('Device Model is: ' + jfacts['model'] + '; and we classify it as a Router...')

    returnVal = update_config(dev,'jnp_config')
    if not isinstance(returnVal, bool):
        if returnVal == 'logical-system':
            pprint('Updated logical_system CFG...')
    elif returnVal == True:
        log.info('Updated CFG...')
    elif returnVal == False:
        log.info('Updated CFG...')

    for reItem in yamlTBL_to_MongoCollections_if_related:
        for item in yamlTBL_to_MongoCollections:
            for jnpPyezTbl in yamlTBL_to_MongoCollections[item]:


                mongoCollection = yamlTBL_to_MongoCollections[item][jnpPyezTbl]
                print jnpPyezTbl, mongoCollection
                print
                if jnpPyezTbl == reItem:
                    retVal = update_data(dev, jnpPyezTbl, mongoCollection)
                    print retVal
                else:
                    pprint(update_data(dev, jnpPyezTbl, mongoCollection))
                    print

    # update_data(dev, 'lldpLocalInfoTable','jnp_lldpLocalInfo',node,node_doc_id)
    # update_data(dev, 'bgpTable', 'jnp_bgpTable', node, node_doc_id)
    #    lldpTBL = update_data(dev,'LLDPNeighborTable', '', node, node_doc_id)
    #    lldpIntDict = dict()
    #    for item in lldpTBL:
    #        lldpIntDict = { 'get': item, 'db_key': 'local_interface', 'db_val': item }
    #        update_data(dev, 'lldpInterfaceTable', 'jnp_lldpInterface', node, node_doc_id, lldpInt

    nodeList = list()

    dev.close()
    log.info("Closing connection to: " + node + ". DONE!")

