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


# Setting up global vars....
SCRIPT_NAME=sys.argv[0]
jfacts = dict()



### ------------------------------------------------------------------------------------------
###                FIRST OF ALL....LOGGING!!!
###                                             <mod by domas.zelionis@enet.ie>
### -------------------------------------------------------------------------------------------
#LOG_LEVEL='ERROR'
LOG_LEVEL='INFO'


timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
log.basicConfig(filename="net_to_db.log", format='%(asctime)s - %(levelname)s - %(message)s', level=getattr(log, LOG_LEVEL))
console = log.StreamHandler()
console.setLevel(getattr(log, LOG_LEVEL))
formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
log.getLogger('').addHandler(console)


### PATH to yaml files
PATH_TO_YAML='junos_yaml/'

# Mongo Database Name:
DATABASE = "test3"
#DATABASE = "north_east"

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
'lldp'          : {'LLDPNeighborTable'  :  'jnp_lldpNeighbors'},
}

# update_data(dev, 'lldpLocalInfoTable','jnp_lldpLocalInfo',node,node_doc_id)
# update_data(dev, 'bgpTable', 'jnp_bgpTable', node, node_doc_id)
#    lldpTBL = update_data(dev,'LLDPNeighborTable', '', node, node_doc_id)
#    lldpIntDict = dict()
#    for item in lldpTBL:
#        lldpIntDict = { 'get': item, 'db_key': 'local_interface', 'db_val': item }
#        update_data(dev, 'lldpInterfaceTable', 'jnp_lldpInterface', node, node_doc_id, lldpInt

nodeList = list()
#nodeList = ["lab.magna.core.vc"]
#nodeList = ["core.mpls.tallaght.acx1"]
#nodeList = ["lab.magna.core.acx"]
#nodeList = ["lab.magna.core.mx5"]
#nodeList = ["core.isp.tcy.gw1"]

#nodeList = ["core.mpls.deg.rtr1"]
#nodeList = ["lab.magna.radio.sw", "lab.magna.core.vc", "lab.magna.radio.ex4300", "lab.magna.test.sw"]
nodeList = ["lab.magna.radio.ex4300", "lab.magna.radio.sw", "lab.magna.core.vc", "lab.magna.test.sw", "lab.magna.access.srx210", "lab.magna.core.acx", "lab.magna.core.mx5"]

#nodeList = ["core.clermont.carn.sw1", "core.metro.hotel.sw1", "core.vdf.carnaross.sw1", "core.eircom4050.sw1", "core.dublin.fibre.vc1", "core.isp.tcy.gw1", "core.telecity.vc1", "core.threerock.coillte.vc1", "core.mpls.deg.rtr1", "core.slieve.glah.sw1", "core.hsq.sw1", "core.isp.deg.gw1", "core.mountoriel.sw1", "core.mpls.tallaght.acx1", "core.tallaght.vc1", "core.mpls.4050.rtr1", "core.mpls.slieve.glah.acx1", "core.deg.sw1", "core.vdf.lisduff.sw1", "core.deg.sw1", "core.vdf.lisduff.sw1", "core.enet.kells.vc1","core.vdf.scotstown.sw1"]





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
        #from include import table
        #tempFunct = getattr(include,table)
    #globals(OpTable(table))
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
    for item in jout:
        # Adding additional fields per document
        jout[item]['node_name'] = jfacts['node_name']
        jout[item]['node_id'] = jfacts['node_doc_id']
        # removing key to get vlan data on the root level and adding it to the list.
        jout_list.append(jout[item])

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

    #return jout_list
    return jout



def update_config(dev, collection):
    global jfacts

    # RPC call to get node configuration in XML format
    try:
        cnf = dev.rpc.get_config(normalize=True)
    except jnpr.junos.exception.RpcError as err:
        log.error('error: Failed to get a CONFIG copy from device: ' + jfacts['node_name']  + '...' + repr(err) + '. Skipping....')
        return False

    #cnf = dev.rpc.get_config(filter_xml=etree.XML('<configuration><interfaces/></configuration>'))
    # Convert XML object into string
#    cnf = False

    if not isinstance(cnf, bool):
        cfg_str = etree.tostring(cnf)
    else:
        cnf = dev.cli("show configuration | no-more | display xml", warning=False)
        pprint(cnf)
        cfg_str = etree.tostring(cnf)
        #return False
    # Convert XML string into JSON dump (string)
    #result = dumps(bf.data(fromstring(cfg_str)))
    result = dumps(parker.data(fromstring(cfg_str), preserve_root=True))

    tmp = list()
    # Remove "." from key values
    result = result.replace("802.3ad", "802_3ad")
    result = result.replace("-802.1", "-802_1")
    # after normalization empty values was replaced with null, replacing null with True to make it more human readable
    #result = result.replace("null", '"true"')
    result = result.replace("null", "true")

    # Convert JSON string into JSON object
    jout = dict()
    jout = json.loads(result)
    # Shift all the data in 'configuration' to the root level.

# Debug for ISP GW will be needed here...
    jout = jout['configuration']
    # Add node_name & node_doc_id to a document
    jout['node_name'] = jfacts['node_name']
    jout['node_id'] = jfacts['node_doc_id']
#
#    pprint(jout['logical-systems']['name'])
    if len(jout) != 0:
        dbCollection = getattr(db, collection)
        dbCollection.remove({'node_name': jfacts['node_name']})

        # Pulling configuration from devices and pushing it to 'config' collection (one document per node)
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
  jfacts = dict() # Cleaning up....

  log.info("NETCONF: connecting to: " + node + "....")
  dev = Device(host=node, user='airspeed', password='', gather_facts=True)
  try:
    dev.open()
  except jnpr.junos.exception.ConnectError as err:
    log.error('error: Failed to connect to: ' + node + '....' + repr(err) + '. Skipping....')
    continue
  else:
    log.info("Collecting facts about device....")
    facts = dev.facts       # Collecting facts about device
    jfactsStr = dumps(facts)        # JSON conversions
    jfacts = loads(jfactsStr)

    jfacts['node_name'] = node      # Adding 'node_name' to facts

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

    # In case it is not a router we are assuming it is a switch.
    # "core.phibsboro.sc.sw1" was an issue wuth macs = get_mac(dev)

    for item in yamlTBL_to_MongoCollections:
        for jnpPyezTbl in yamlTBL_to_MongoCollections[item]:
            mongoCollection = yamlTBL_to_MongoCollections[item][jnpPyezTbl]
            print jnpPyezTbl, mongoCollection
            print
            pprint(update_data(dev, jnpPyezTbl, mongoCollection))
            print

#    update_config(dev,'jnp_config',node,node_doc_id)

    # PhyPortStatsTable InterfacesTBL  EthPortTable

    #print(jfacts['model'])
    # In case it is a router (L3)

    #db.nodes.aggregate([{$match:{ 'node_name':'lab.magna.test.sw'}},{$project:{ 'facts':0 }},{$lookup:{ from: "vlans", localField: "vlans_id", foreignField: "_id", as: "vlans"}},{$unwind : "$vlans"}])

    dev.close()
    log.info("Closing connection to: " + node + ". DONE!")

