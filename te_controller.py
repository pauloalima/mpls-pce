__author__ = 'dipsingh'

import socket
import mpls_lsp_pb2
import struct


class TEController(object):
    def __init__(self):
        self._lsp_dict = dict()
        self._srpid = 1

    def ip2int(self, addr):
        return struct.unpack_from("!I", socket.inet_aton(addr))[0]

    def handle_pce_message(self, pcc_ip, message):
        if message[0] == 'State_Report':
            result = self.handle_state_report_od(pcc_ip, message)
            return result
        return (None,)

    def handle_state_report_od(self,pcc_ip,message):
        lsp=mpls_lsp_pb2.LSP()
        first_lsp = 1
        for report_object in message[1]:
            if (report_object[0] == 'LSP_Object'):
                if (report_object[1][0] != 0):
                    lsp.pcc_ip = pcc_ip[0]
                    lsp.lsp_obj.plsp_id = report_object[1][0]
                    lsp.lsp_obj.delegated = report_object[1][1]
                    lsp.lsp_obj.sync = report_object[1][2]
                    lsp.lsp_obj.remove = report_object[1][3]
                    lsp.lsp_obj.administrative = report_object[1][4]
                    lsp.lsp_obj.operational = report_object[1][5]
                    lsp.lsp_obj.create = report_object[1][6]
            if report_object[0] == "Bandwidth_Object" :
                lsp.bandwidth = report_object[1][0]
            if report_object[0] == "SRP_ID":
                lsp.srp.srp_id = report_object[1][0]
            if report_object[0] == "LSPA":
                lsp.lspa_obj.setup_prio= report_object[1][0]
                lsp.lspa_obj.hold_prio = report_object[1][1]
                lsp.lspa_obj.local_protection = report_object[1][2]
            if report_object[0] == "ERO_List" :
                if len(report_object[1]) > 0 :
                    for ero_node in report_object[1]:
                        ero=lsp.ero.add()
                        ero.loose= ero_node[1]
                        ero.node_ip = ero_node[2]
                        ero.node_mask= ero_node[3]
            if report_object[0] == "SR_ERO_lIST":
                if len(report_object[1]) > 0:
                    for ero_node in report_object[1]:
                        srero = lsp.srero.add()
                        srero.loose = ero_node[1]
                        srero.node_label = ero_node[2]
                        srero.node_ip = ero_node[3]
            if report_object[0] == "RRO_List":
                if len (report_object[1]) > 0 :
                    for rro_node in report_object[1]:
                        rro=lsp.rro.add()
                        rro.loose=rro_node[1]
                        rro.node_ip = rro_node[2]
                        rro.node_mask = rro_node[3]
        lsp_dict_index = (self.ip2int(pcc_ip[0]),lsp.lsp_obj.plsp_id)
        self._lsp_dict[lsp_dict_index] = lsp
        delegate_lsps = list()
        for key in self._lsp_dict:
            lsp = self._lsp_dict[key]
            if (lsp.lsp_obj.delegated) & (self._srpid!=lsp.srp.srp_id):
                delegate_lsps.append(lsp)
                print ("Delegated LSP ", lsp)
        self._srpid = lsp.srp.srp_id
        if len (delegate_lsps) > 0:
            resp = list()
            for lsp in delegate_lsps:
                resp.extend(self.generate_lsp_upd_msg_od(lsp))
            print ("Delegated LSPs RESP", resp)
            #return ("lsp_update",resp)
        return (None)

    def generate_lsp_upd_msg_od(self,lsp):
        upd_msg = list()
        upd_msg.append(('LSP_Object',(lsp.lsp_obj.plsp_id,lsp.lsp_obj.delegated,lsp.lsp_obj.sync,lsp.lsp_obj.remove,lsp.lsp_obj.administrative,lsp.lsp_obj.operational)))
        if lsp.ero:
            ero_list = list()
            for ero in lsp.ero:
                ero_list.append((ero.loose,self.ip2int(ero.node_ip),ero.node_mask))
            upd_msg.append(("ERO_List",ero_list))
        else:
            upd_msg.append (("ERO_List",((0,0,0),)))
        upd_msg.append (("LSPA",(lsp.lspa_obj.setup_prio,lsp.lspa_obj.hold_prio,lsp.lspa_obj.local_protection)))
        upd_msg.append (("Bandwidth_Object",(lsp.bandwidth,)))
        return (upd_msg)



















