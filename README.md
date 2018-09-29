# JunOS-and-MongoDB

It's a working Version of a script for collection all the possible data from Juniper devices (including configuration) using Netconf and Juniper Pyez libraries and push/store it on MongoDB (in JASON style). 
All the tables was customized to meet item per node per document database schema (for example for mac table, one document per mac-address per node will be created in collection, or per node per LSP) , also to get most of the data of the Juniper routers and switches. Some tables still in the progress...

domas@ras-linux:~$mongo test3
MongoDB shell version v4.0.2
connecting to: mongodb://127.0.0.1:27017/test3
MongoDB server version: 4.0.2

> show collections
jnp_arpTable
jnp_chassisInv
jnp_config
jnp_fpcHW
jnp_fpcInfo
jnp_fpcMiReHW
jnp_fpcMiReInfo
jnp_intDesc
jnp_intExtensive
jnp_intMedia
jnp_interface
jnp_isisAdjacency
jnp_l2vpn
jnp_lacpPort
jnp_lldpInterface
jnp_lldpLocalInfo
jnp_lldpNeighbors
jnp_macTable
jnp_mplsLsp
jnp_rsvpInterface
jnp_rsvpNeighbor
jnp_rsvpSession
jnp_vlans
jnp_xcvr
nodes


> db.jnp_mplsLsp.findOne({"node_name":"lab.magna.core.acx"})
{
	"_id" : ObjectId("5baeeb0412040f35ef855b43"),
	"lsp_description" : "lsp-description",
	"active_path" : "(primary)",
	"egress_label_operation" : "Penultimate hop popping",
	"session_type" : "Ingress",
	"lsp_name" : "lab.magna.core.acx-to-router_e",
	"node_name" : "lab.magna.core.acx",
	"lsp_type" : "Static Configured",
	"node_id" : ObjectId("5badce7b12040f6b59d805f0"),
	"lsp_path" : {
		"('Primary',)" : {
			"setup_priority" : "7",
			"hold-priority" : "0",
			"title" : "Primary",
			"name" : [
				"Primary"
			],
			"explicit_route" : {
				"Primary" : {
					"address" : [
						"192.168.4.10",
						"S"
					]
				}
			},
			"smart_optimize_timer" : "180",
			"cspf_status" : "Computed ERO (S [L] denotes strict [loose] hops): (CSPF metric: 10)",
			"received_rro" : "Received RRO (ProtectionFlag 1=Available 2=InUse 4=B/W 8=Node 10=SoftPreempt 20=Node-ID): 192.168.4.10",
			"path_history" : {
				"1" : {
					"route" : "route",
					"log" : "CSPF failed: no route toward 192.168.12.4",
					"sequence_number" : "1",
					"time" : "Jul 4 13:11:54.874"
				},
				"3" : {
					"route" : "route",
					"log" : "Originate Call",
					"sequence_number" : "3",
					"time" : "Jul 4 13:12:24.008"
				},
				"2" : {
					"route" : "192.168.4.10",
					"log" : "CSPF: computation result accepted",
					"sequence_number" : "2",
					"time" : "Jul 4 13:12:24.008"
				},
				"5" : {
					"route" : "192.168.4.10",
					"log" : "Record Route:",
					"sequence_number" : "5",
					"time" : "Jul 4 13:12:24.015"
				},
				"4" : {
					"route" : "route",
					"log" : "Up",
					"sequence_number" : "4",
					"time" : "Jul 4 13:12:24.015"
				},
				"6" : {
					"route" : "route",
					"log" : "Selected as active path",
					"sequence_number" : "6",
					"time" : "Jul 4 13:12:24.016"
				}
			},
			"path_active" : "path-active",
			"path_state" : "Up"
		}
	},
	"load_balance" : "random",
	"destination_address" : "192.168.12.4",
	"source_address" : "192.168.12.3",
	"route_count" : "0",
	"lsp_creation_time" : "Wed Jul 4 13:11:26 2018",
	"lsp_state" : "Up"
}

> db.jnp_lldpInterface.findOne({"node_name":"lab.magna.core.vc"})
{
	"_id" : ObjectId("5bae406c12040f78ed445217"),
	"remote_system_capabilities_supported" : "Bridge Router",
	"local_interface" : "ge-1/0/1.0",
	"ttl" : "120",
	"remote_management_address_interface_subtype" : "ifIndex(2)",
	"index" : "517",
	"timemark" : "Fri Sep 28 14:53:20 2018",
	"remote_system_description" : "Juniper Networks, Inc. mx5-t , version 13.3R6.5 Build date: 2015-03-26 20:31:28 UTC",
	"remote_chassis_id" : "08:b2:58:bc:c8:c0",
	"remote_management_addr_oid" : "1.3.6.1.2.1.31.1.1.1.1.1",
	"local_parent_interface_name" : "-",
	"remote_chassis_id_subtype" : "Mac address",
	"remote_port_description" : "[router_e][Trunk] to lab.magna.core.vc ge-1/0/1",
	"remote_port_id" : "ge-1/1/1",
	"remote_port_id_subtype" : "Interface name",
	"local_port_id" : "618",
	"remote_management_address" : "10.4.0.94",
	"node_id" : ObjectId("5badce5912040f6b59d804c7"),
	"remote_management_address_port_id" : "1",
	"local_port_ageout_count" : "0",
	"remote_system_name" : "lab.magna.core.mx5",
	"remote_system_capabilities_enabled" : "Bridge Router",
	"age" : "12",
	"node_name" : "lab.magna.core.vc",
	"remote_management_address_type" : "IPv4",
	"remote_management_address_sub_type" : "1"
}

> db.jnp_lldpNeighbors.findOne({"node_name":"lab.magna.core.vc"})
{
	"_id" : ObjectId("5baeead012040f35ef855998"),
	"remote_port_id" : null,
	"remote_port_desc" : "[router_e][Trunk] to lab.magna.core.vc ge-1/0/1",
	"local_int" : "ge-1/0/1.0",
	"remote_sysname" : "lab.magna.core.mx5",
	"local_parent" : "-",
	"node_id" : ObjectId("5badce5912040f6b59d804c7"),
	"remote_chassis_id" : "08:b2:58:bc:c8:c0",
	"remote_type" : "Mac address",
	"node_name" : "lab.magna.core.vc"
}

> db.jnp_intDesc.findOne({'node_name':'lab.magna.radio.sw'})
{
	"_id" : ObjectId("5baeeab412040f35ef8557be"),
	"oper" : "up",
	"description" : "[mngm] [xxx.xxx.xxx.xxx v333]",
	"admin" : "up",
	"node_name" : "lab.magna.radio.sw",
	"node_id" : ObjectId("5badce5012040f6b59d8049c"),
	"interface" : "ge-0/0/7"
}




> db.jnp_config.findOne({'node_name':'lab.magna.test.sw'})
{
	"_id" : ObjectId("5baeead812040f35ef855a7e"),
	"ethernet-switching-options" : {
		"dot1q-tunneling" : {
			"ether-type" : "0x8100"
		}
	},
	"node_id" : ObjectId("5badce6412040f6b59d805cc"),
	"chassis" : {
		"aggregated-devices" : {
			"ethernet" : {
				"device-count" : 4
			}
		}
	},
	"snmp" : {
		"contact" : "domas.zelionis@enet.ie",
		"location" : "LAB.magna.test.sw",
		"community" : {
			"clients" : [
				{
					"name" : "10.4.0.0/24"
				},
				{
					"name" : "10.0.0.0/8"
				}
			],
			"name" : "public",
			"authorization" : "read-only"
		},
	},
	"interfaces" : {
		"interface" : [
			{
				"name" : "ge-0/0/0",
				"unit" : {
					"name" : 0,
					"family" : {
						"ethernet-switching" : {
							"port-mode" : "trunk",
							"vlan" : {
								"members" : "v50"
							}
						}
					}
				},
				"description" : "[Trunk] to lab.magna.access.srx210 fe-0/0/6"
			},
			{
				"name" : "ge-0/0/22",
				"unit" : {
					"name" : 0,
					"family" : {
						"ethernet-switching" : {
							"port-mode" : "trunk",
							"vlan" : {
								"members" : "v50"
							}
						}
					}
				},
				"description" : "[Trunk] to lab.magna.core.vc ge-1/0/22"
			},
			{
				"name" : "me0",
				"unit" : {
					"name" : 0,
					"family" : {
						"inet" : {
							"address" : {
								"name" : "10.4.0.88/24"
							}
						}
					}
				}
			}
		]
	},
	"routing-options" : {
		"static" : {
			"route" : {
				"next-hop" : "10.4.0.1",
				"name" : "0.0.0.0/0"
			}
		}
	},
	"system" : {
		"name-server" : [
			{
				"name" : "10.4.0.16"
			},
			{
				"name" : "8.8.8.8"
			}
		],
		"syslog" : {
			"user" : {
				"name" : "*",
				"contents" : {
					"name" : "any",
					"emergency" : true
				}
			},
			"file" : [
				{
					"name" : "messages",
					"contents" : [
						{
							"notice" : true,
							"name" : "any"
						},
						{
							"info" : true,
							"name" : "authorization"
						}
					]
				},
				{
					"name" : "interactive-commands",
					"contents" : {
						"name" : "interactive-commands",
						"any" : true
					}
				}
			]
		},
		"host-name" : "lab.magna.test.sw",
		"services" : {
			"netconf" : {
				"ssh" : true
			},
			"web-management" : {
				"http" : true
			},
			"ssh" : true,
			"telnet" : true
		},
		"commit" : {
			"synchronize" : true
		},
		"login" : {
			"class" : [
				{
					"name" : "tier1",
					"permissions" : "snmp"
				},
				{
					"name" : "tier2",
					"permissions" : [
						"snmp",
						"snmp-control"
					]
				}
			],
	},
	"node_name" : "lab.magna.test.sw",
	"version" : "12.3R12.4",
	"vlans" : {
		"vlan" : [
			{
				"vlan-id" : 111,
				"name" : "v111",
				"description" : "[LAN ] Magna [DHCP 10.4.0.0/24]"
			},
			{
				"vlan-id" : 123,
				"name" : "v123",
				"description" : "TEST"
			},
			{
				"vlan-id" : 333,
				"name" : "v333",
				"description" : "Ceragon management"
			},
			{
				"vlan-id" : 50,
				"name" : "v50",
				"description" : "Customer 50"
			},
			{
				"vlan-id" : 91,
				"name" : "v91",
				"description" : "Tester's stream to nokia"
			}
		]
	},
	"protocols" : {
		"lldp" : {
			"interface" : [
				{
					"name" : "ge-0/0/22.0"
				},
				{
					"name" : "ge-0/0/0.0"
				}
			],
			"port-description-type" : "interface-description",
			"port-id-subtype" : "interface-name",
			"management-address" : "10.4.0.88"
		}
	}
}




