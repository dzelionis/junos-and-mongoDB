from jnpr.junos import Device
import jnpr.junos.exception
import jnpr.junos.factory as FactoryLoader

from jnpr.junos.op.arp import ArpTable
from jnpr.junos.op.ccc import CCCTable
from jnpr.junos.op.ethport import EthPortTable
from jnpr.junos.op.isis import IsisAdjacencyTable
from jnpr.junos.op.l2circuit import L2CircuitConnectionTable
from jnpr.junos.op.lacp import LacpPortTable
from jnpr.junos.op.phyport import PhyPortTable
from jnpr.junos.op.phyport import PhyPortStatsTable
from jnpr.junos.op.routes import RouteTable
from jnpr.junos.op.fpc import FpcHwTable
from jnpr.junos.op.fpc import FpcMiReHwTable
from jnpr.junos.op.fpc import FpcInfoTable
from jnpr.junos.op.fpc import FpcMiReInfoTable
from jnpr.junos.op.inventory import ModuleTable

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



PATH_TO_YAML='junos_yaml/'
YAML_FILES_TO_LOAD='ethernetswitchingtable','vlan','lldp'




for item in YAML_FILES_TO_LOAD:
  globals().update(FactoryLoader.loadyaml(PATH_TO_YAML + item + '.yml'))


# Configure logging to file and console
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#log.basicConfig(filename="%slogs/%s_%s.log" % (WD,sys.argv[0],timestamp), format='%(asctime)s - %(levelname)s - %(message)s', level=log.INFO)
log.basicConfig(filename="net_to_db.log", format='%(asctime)s - %(levelname)s - %(message)s', level=log.INFO)
console = log.StreamHandler()
console.setLevel(log.INFO)
formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
log.getLogger('').addHandler(console)



nodeList = list()
#nodeList = ["lab.magna.radio.sw", "lab.magna.core.vc", "lab.magna.radio.ex4300", "lab.magna.test.sw"]
nodeList = ["lab.magna.radio.ex4300", "lab.magna.radio.sw", "lab.magna.core.vc", "lab.magna.test.sw", "lab.magna.access.srx210", "lab.magna.core.acx", "lab.magna.core.mx5"]

#nodeList = ["core.clermont.carn.sw1", "core.metro.hotel.sw1", "core.vdf.carnaross.sw1", "core.eircom4050.sw1", "core.dublin.fibre.vc1", "core.isp.tcy.gw1", "core.telecity.vc1", "core.threerock.coillte.vc1", "core.mpls.deg.rtr1", "core.slieve.glah.sw1", "core.hsq.sw1", "core.isp.deg.gw1", "core.mountoriel.sw1", "core.mpls.tallaght.acx1", "core.tallaght.vc1", "core.mpls.4050.rtr1", "core.mpls.slieve.glah.acx1", "core.deg.sw1", "core.vdf.lisduff.sw1"]
#nodeList = ["core.deg.sw1", "core.vdf.lisduff.sw1"]
#nodeList = ["core.enet.kells.vc1","core.vdf.scotstown.sw1"]

# MongoDB Driver

# Changing database to
DATABASE = "test3"
#DATABASE = "north_east"

try:
    dbclient = MongoClient('localhost', 27017)
except pymongo.errors.ServerSelectionTimeoutError as err:
    log.critical("ERROR: failed to connect to DB (" + repr(err) + ")")
    log.critical("ERROR: Exiting....")
    exit(1)

db = getattr(dbclient, DATABASE)
log.info("Connected to MongoDB, using database: " + DATABASE + "...")



def update_data(dev, table, collection, node, node_doc_id, options=''):
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
        jout[item]['node_name'] = node
        jout[item]['node_id'] = node_doc_id
        # removing key to get vlan data on the root level and adding it to the list.
        jout_list.append(jout[item])

    if len(jout_list) != 0:
        dbCollection = getattr(db, collection)
        if isinstance(options, dict):
            if options['db_key'] and options['db_val']:
                dbCollection.remove({'node_name': node, options['db_key']: options['db_val']})
            else:
                dbCollection.remove({'node_name': node})
        else:
            dbCollection.remove({'node_name': node})
        print dbCollection.insert(jout_list)

    #return jout_list
    return jout



def update_config(dev, collection, node, node_doc_id):

    if node == "core.isp.tcy.gw1" or node == "core.isp.deg.gw1":
        conf = dict()
        return conf


    # RPC call to get node configuration in XML format
    cnf = dev.rpc.get_config(normalize=True)

    #cnf = dev.rpc.get_config(filter_xml=etree.XML('<configuration><interfaces/></configuration>'))

    # Convert XML object into string
    cfg_str = etree.tostring(cnf)

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
    jout = json.loads(result)
    # Shift all the data in 'configuration' to the root level.
    jout = jout['configuration']
    # Add node_name & node_doc_id to a document
    jout['node_name'] = node
    jout['node_id'] = node_doc_id

    if len(jout) != 0:
        dbCollection = getattr(db, collection)
        dbCollection.remove({'node_name': node})

        # Pulling configuration from devices and pushing it to 'config' collection (one document per node)
        configuration_doc_id = dbCollection.insert_one(jout).inserted_id
    return jout




for node in nodeList:
  nodeExistsInDb = False
  log.info("NETCONF: connecting to: " + node + "....")
  dev = Device(host=node, user='airspeed', password='', gather_facts=True)
  try:
    dev.open()
  except jnpr.junos.exception.ConnectError as err:
    log.error('error: Failed to connect to: ' + node + '(' + repr(err) + ')')
    log.error('error: Skipping....')
    continue
  else:

    facts = dev.facts       # Collecting facts about device
    jfactsStr = dumps(facts)        # JSON conversions

    print "collecting data...."

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
    #    print node_id

    # Pushing  facts into 'nodes' collection, one document per node

    node_doc_id = db.nodes.insert_one(jfacts).inserted_id

    # pprint(lldpLocalInfoTable)EtherSwTable
    update_data(dev, 'lldpLocalInfoTable','jnp_lldpLocalInfo',node,node_doc_id)
    # pprint(update_data(dev,'EtherSwTableV200', 'jnp_macTable', node, node_doc_id))
    update_data(dev, 'EtherSwTableV200', 'jnp_macTable', node, node_doc_id)
    update_data(dev, 'VlanDetailTable', 'jnp_vlans', node, node_doc_id)

    update_data(dev, 'L2CircuitConnectionTable', 'jnp_l2vpn',node,node_doc_id)
    update_data(dev, 'CCCTable','jnp_cccInfo',node,node_doc_id)

    update_data(dev, 'ArpTable', 'jnp_arpTable', node, node_doc_id)
    update_data(dev, 'IsisAdjacencyTable', 'jnp_isisAdjacency', node, node_doc_id)
    #update_data(dev, 'bgpTable', 'jnp_bgpTable', node, node_doc_id)

    #update_data(dev, '', 'jnp_', node, node_doc_id)
    #update_data(dev, '', 'jnp_', node, node_doc_id)
    #update_data(dev, '', 'jnp_', node, node_doc_id)

    lldpTBL = update_data(dev,'LLDPNeighborTable', 'jnp_lldpNeighbors', node, node_doc_id)

    lldpIntDict = dict()
    for item in lldpTBL:
        lldpIntDict = { 'get': item, 'db_key': 'local_interface', 'db_val': item }
        update_data(dev, 'lldpInterfaceTable', 'jnp_lldpInterface', node, node_doc_id, lldpIntDict)

    update_config(dev,'jnp_config',node,node_doc_id)

    # PhyPortStatsTable InterfacesTBL  EthPortTable

    #print(jfacts['model'])
    # In case it is a router (L3)
    if jfacts['model'] == "ACX1100" or jfacts['model'] == "MX5-T":
        print "Router"
    # In case it is not a router we are assuming it is a switch.
    # "core.phibsboro.sc.sw1" was an issue wuth macs = get_mac(dev)


    #db.nodes.aggregate([{$match:{ 'node_name':'lab.magna.test.sw'}},{$project:{ 'facts':0 }},{$lookup:{ from: "vlans", localField: "vlans_id", foreignField: "_id", as: "vlans"}},{$unwind : "$vlans"}])

    dev.close()
    log.info("Closing connection to: " + node + ". DONE!")

