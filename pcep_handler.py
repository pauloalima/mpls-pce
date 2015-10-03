__author__ = 'dipsingh'

import string
import struct
import socket
import binascii
import json

class PCEP(object):

   """ 6.1.  Common Header
     0                   1                   2                   3
     0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    | Ver |  Flags  |  Message-Type |       Message-Length          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    Common Object Header:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Object-Class  |   OT  |Res|P|I|   Object Length (bytes)       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   //                        (Object body)                        //
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

   Open Object Format:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Ver |   Flags |   Keepalive   |  DeadTimer    |      SID      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   //                       Optional TLVs                         //
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
   def __init__(self,open_sid = 0):
       self._common_hdr_format = '!BBH'
       self._common_obj_hdr_format= '!BBH'
       self._open_obj_format = '!BBBB'
       self._spc_tlv = struct.pack("!HHI",16,4,5)
       self._spc_sr_tlv = struct.pack("!HHI",26,4,10)
       self._spc_sr_tlv_format = "!HHI"
       self._symbolic_path_name_tlv = '!HH8s'
       self._state = 'not_initialized'
       self._lsp_obj_fmt = "!I"
       self._lspa_obj_fmt = "!IIIBBBB"
       self._bw_obj_fmt = "!I"
       self._error_obj_fmt = "!BBBB"
       self._srp_obj_fmt = "!II"
       self._srp_id = 1
       self._endpoint_obj_fmt = "!II"
       self._open_object_SID = 0
       self._state = 'not initialzied'
       self._functions_dict = dict()
       '''self._functions_dict[4,1] = self.parse_endpoints_object'''
       self._functions_dict[5,1] = self.parse_bw_object
       self._functions_dict[5,2] = self.parse_bw_object
       '''self._functions_dict[6,1] = self.parse_metric_object'''
       self._functions_dict[7,1] = self.parse_ero_object
       '''self._functions_dict[8,1] = self.parse_rro_object'''
       self._functions_dict[9,1] = self.parse_lspa_object
       self._functions_dict[32,1] = self.parse_lsp_object_od
       self._functions_dict[33,1] = self.parse_srp_object


   def ip2int(self, addr):
       return struct.unpack_from("!I", socket.inet_aton(addr))[0]

   def int2ip(self,addr):
        return socket.inet_ntoa(struct.pack("!I",addr))

   def parse_recvd_msg(self,msg):
       common_hdr = struct.unpack(self._common_hdr_format,msg[0:4])
       if common_hdr[1] == 1:
           print('Open msg recved')
           self.parse_open_msg(common_hdr,msg)
       if common_hdr[1] == 2:
           print('Keepalive msg recved')
           self.parse_ka_msg(common_hdr,msg)
       if common_hdr[1] == 3:
           print('Path Computation Request recved')
       if common_hdr[1] == 4:
           print('Path Computation Reply recved')
       if common_hdr[1] == 5:
           print('Notification recved')
       if common_hdr[1] == 6:
           print('Error msg recved')
           return self.parse_error_msg(common_hdr,msg)
       if common_hdr[1] == 7:
           print('Close msg recved')
       if common_hdr[1] == 10:
           print('PCC State report msg recved')
           return self.parse_state_report_msg(common_hdr,msg)
       elif common_hdr[1] == 11:
           print('pcc update msg recved')
       return ('Not Implemented yet',None)

   '''
       Common Object Header:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Object-Class  |   OT  |Res|P|I|   Object Length (bytes)       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   //                        (Object body)                        //
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   '''
   def parse_common_obj_hdr(self,msg,offset=0):
       common_obj_hdr = struct.unpack_from(self._common_obj_hdr_format,msg[4+offset:])
       object_class = common_obj_hdr[0]
       object_length = common_obj_hdr[2]
       object_type = common_obj_hdr[1] >> 4
       #3 = 0000 0011
       object_flag_PI = common_obj_hdr[1] & 3
       print ("Object Class %s, Object Type %s and Object Length %s "% (object_class,object_type,object_length))
       return (object_class,object_type,object_flag_PI,object_length)

   """Open Object Format:
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Ver |   Flags |   Keepalive   |  DeadTimer    |      SID      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   //                       Optional TLVs                         //
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   """
   def parse_open_msg(self,common_hdr,msg):
       self.parse_common_obj_hdr(msg)
       common_object_body = struct.unpack_from(self._open_obj_format,msg[8:])
       self._open_object_SID = common_object_body[3]
       open_object_DeadTimer = common_object_body[2]
       self._peer_ka_timer = common_object_body[1]
       open_object_version = common_object_body[0] >> 5
       print ("SID Is %s "%(self._open_object_SID))
       if (common_hdr[2] > 12):
           print ("StateFul Capabiity Support ")
       if (common_hdr[2] > 20):
           print ("SR Capability Support Too")
       self._state='initialized'
       return (self._open_object_SID)

   def parse_ka_msg(self,common_hdr,msg):
       print ("KA MSG")

   '''
     0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                PLSP-ID                |   Flags |C|  O|A|R|S|D|
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     //                        TLVs                                 //
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

   '''

   def parse_lsp_object_od(self, msg, com_obj_hdr, offset=0):
       lsp_obj = struct.unpack_from(self._lsp_obj_fmt,msg[8+offset:])
       plsp_id = lsp_obj[0] >> 12
       c_flag=d_flag=s_flag=r_flag=a_flag=o_flag = 0
       print ("Lenght of common_obj_hdr",com_obj_hdr)
       if (lsp_obj[0] & 1):
           d_flag = 1
       if (lsp_obj[0] & 2):
           s_flag = 1
       if (lsp_obj[0] & 4):
           r_flag = 1
       if (lsp_obj[0] & 8):
           a_flag = 1
       if (lsp_obj[0] & 112):
           o_flag = 1
       if (lsp_obj[0] & 128):
           c_flag = 1
       if com_obj_hdr[3] > 8:
           print('lsp_obj has TLVs')
           ipv4_lsp_identifier_type_length = struct.unpack_from("!HH",msg[12+offset:])
           ipv4_lsp_identifier_tunnel_sender = struct.unpack_from("8c",msg[16+offset:])
           print ("Signalled Tunnel Name",b"".join((ipv4_lsp_identifier_tunnel_sender[0],
                                           ipv4_lsp_identifier_tunnel_sender[1],
                                           ipv4_lsp_identifier_tunnel_sender[2],
                                           ipv4_lsp_identifier_tunnel_sender[3],
                                           ipv4_lsp_identifier_tunnel_sender[4],
                                           ipv4_lsp_identifier_tunnel_sender[5],
                                           ipv4_lsp_identifier_tunnel_sender[6],
                                           ipv4_lsp_identifier_tunnel_sender[7])))
            #TODO: add tlv's parsing
       return ('LSP_Object',(plsp_id,d_flag,s_flag,r_flag,a_flag,o_flag,c_flag))

   def parse_state_report_msg(self,common_hdr,msg):
       offset = 0
       parsed_state_report = list()
       while (offset+4) < common_hdr[2] :
           parsed_obj_header = self.parse_common_obj_hdr(msg,offset)
           if (parsed_obj_header[0],parsed_obj_header[1]) in self._functions_dict:
               oc_ot= (parsed_obj_header[0],parsed_obj_header[1])
               parsed_obj = self._functions_dict[oc_ot](msg,parsed_obj_header,offset)
               parsed_state_report.append(parsed_obj)
           else:
               parsed_state_report.append(("unknown obj",))
           offset = offset+parsed_obj_header[3]
           print ("Offset VAlue is ",offset)
       print ("Parsed State Report",parsed_state_report)
       return ("State_Report",parsed_state_report)

   def parse_ero_subobject(self,ero_obj):
       tlv_type = struct.unpack_from("!BB",ero_obj)
       loose_hop_flag = tlv_type[0] >> 7
       sobj_type = tlv_type[0] & 127
       sobj_length = tlv_type[1]
       if sobj_type == 1 :
           ero_sobj = struct.unpack_from("!BBIBB",ero_obj)
           ero_sobj_ipv4_add = ero_sobj[2]
           ero__sobj_ipv4_len = ero_sobj[3]
           return (sobj_length,loose_hop_flag,socket.inet_ntoa(struct.pack("!I",ero_sobj_ipv4_add)),ero__sobj_ipv4_len)
       else :
           return (1000,None,None)

       """
        0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |L|    Type     |     Length    | IPv4 address (4 bytes)        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | IPv4 address (continued)      | Prefix Length |      Resvd    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

"""

   def parse_ero_object(self,msg,com_obj_hdr,offset=0):
       parsed_ero_size = 0
       ero_list = list ()
       while (parsed_ero_size + 4) < com_obj_hdr[3]:
           sub_obj = self.parse_ero_subobject(msg[offset+8+parsed_ero_size:])
           parsed_ero_size += sub_obj[0]
           ero_list.append(sub_obj)
       return ("ERO_List",(ero_list))

   def parse_lspa_object(self,msg,com_obj_hdr,offset=0):
       lspa_obj = struct.unpack_from(self._lspa_obj_fmt,msg[offset+8:])
       setup_pri = lspa_obj[3]
       hold_pri = lspa_obj[4]
       L_flag = lspa_obj[5]&1
       print ("lspa obj is %s %s %s" %(setup_pri,hold_pri,L_flag))
       return ('LSPA',(setup_pri,hold_pri,L_flag))

   def parse_bw_object(self,msg,com_obj_hdr,offset=0):
       bw_obj = struct.unpack_from(self._bw_obj_fmt,msg[offset+8:])
       print (bw_obj)
       return ("Bandwidth_Object",(bw_obj[0],))

   def parse_error_msg(self,common_hdr,msg):
       self.parse_common_obj_hdr(msg)
       error_msg = struct.unpack_from(self._error_obj_fmt,msg[8:])
       error_type = error_msg[2]
       error_value = error_msg[3]
       print ("Error Receieved")
       print ("Error Type and Value is ", error_type,error_value)

   '''
        0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                          Flags                                |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                        SRP-ID-number                          |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                                                               |
      //                      Optional TLVs                          //
      |                                                               |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   '''

   def parse_srp_object(self,msg,common_obj_hdr,offset=0):
       size = 8
       print ("Before unpacking",msg[offset+8:8])
       unpacked_obj = struct.unpack_from(self._srp_obj_fmt,msg[offset+8:])
       srp_id = unpacked_obj[1]
       print (" Here is the Unpacked OBJ and SRP ID ",unpacked_obj,srp_id)
       return ('SRP_ID',(srp_id,0))

   def parse_ka_msg(self,common_hdr,msg):
       return ("KA MSG")

   def generate_open_msg(self,ka_timer):
       self._ka_timer= ka_timer
       common_hdr = struct.pack("!BBH",32,1,28)
       common_obj_hdr= struct.pack("!BBH",1,16,24)
       open_object = struct.pack(self._open_obj_format,32,self._ka_timer,4*self._ka_timer,self._open_object_SID)
       print ("Sending Open Message to PCC")
       return b"".join((common_hdr,common_obj_hdr,open_object,self._spc_tlv,self._spc_sr_tlv))

   '''
   def generate_sr_open_msg(self,ka_timer):
       self._ka_timer = ka_timer
       common_hdr = struct.pack("!BBH",32,1,28)
       common_obj_hdr = struct.pack("!BBH",1,16,24)
       open_object = struct.pack(self._open_obj_format,32,self._ka_timer,4*self._ka_timer,self._open_object_SID)
       print ("Sending Open Message to PCC with SR")
       retunr b"".join((common_hdr,common_obj_hdr,open_object,self._spc_tlv,self._spc_sr_tlv))
   '''

   def generate_ka_msg(self):
       keepalive_msg = struct.pack(self._common_hdr_format,32,2,4)
       print ("Sending Keep Alive Message")
       return (keepalive_msg)

   def generate_common_obj_hdr(self,oc,ot,length,PI_flags=0):
       return struct.pack(self._common_obj_hdr_format,oc,((ot<<4)|PI_flags),length)

   '''
        0                   1                   2                   3
       0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                          Flags                                |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                        SRP-ID-number                          |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                                                               |
      //                      Optional TLVs                          //
      |                                                               |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

   '''

   def generate_sr_srp_object(self,srp_id):
       size = 8
       packed_obj = struct.pack(self._srp_obj_fmt,0,srp_id)
       packed_common_hdr = self.generate_common_obj_hdr(33,1,size+4,2)
       return (size+4,b"".join((packed_common_hdr,packed_obj)))

   def generate_srp_object(self,srp_id):
       size = 8
       packed_obj = struct.pack(self._srp_obj_fmt,0,srp_id)
       packed_common_hdr = self.generate_common_obj_hdr(33,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_obj)))



   '''
    0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                PLSP-ID                |   Flags |C|  O|A|R|S|D|
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     //                        TLVs                                 //
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   '''

   def generate_lsp_obj(self,obj):
       plsp_id = obj[0]
       d_flag = obj[1]
       s_flag = obj[2]
       r_flag = 0
       a_flag = 1
       o_flag = obj[5]
       summary_obj = plsp_id << 12
       summary_obj |= (d_flag | (s_flag << 1) | (r_flag<<2) | (a_flag << 3) |o_flag << 4)
       size = 4
       packed_obj = struct.pack("!I",summary_obj)
       packed_common_hdr = self.generate_common_obj_hdr(32,1,size+4)
       print ("PLSP ID from Generate LSP and D Flag",plsp_id,d_flag)
       return (size+4,b"".join((packed_common_hdr,packed_obj)))

   '''
   0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                PLSP-ID                |   Flags |C|  O|A|R|S|D|
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     //                        TLVs                                 //
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

       0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |           Type=[TBD]          |       Length (variable)       |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                                                               |
     //                      Symbolic Path Name                     //
     |                                                               |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     Type=17
   '''

   def generate_pceint_lsp_obj(self,TUNNEL_NAME):
       plspd_id = 0
       d_flag=1
       s_flag=0
       r_flag=0
       a_flag=1
       o_flag=0
       c_flag=1
       summary_obj = plspd_id << 12
       summary_obj |= (d_flag | (s_flag << 1) | (r_flag<<2) | (a_flag << 3) | (o_flag << 4)  )
       size = 16 #Length + 4
       SYMBOLIC_PATH_NAME= TUNNEL_NAME
       symbolic_packed_obj = struct.pack(self._symbolic_path_name_tlv,17,len(SYMBOLIC_PATH_NAME), SYMBOLIC_PATH_NAME)
       packed_obj = struct.pack("!I",summary_obj)
       packed_common_hdr = self.generate_common_obj_hdr(32,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_obj,symbolic_packed_obj)))


   '''
        0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |L|    Type     |     Length    | IPv4 address (4 bytes)        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | IPv4 address (continued)      | Prefix Length |      Resvd    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

   '''

   def generate_ero_subobject(self,ero_subobj):
       size = 8
       subobj_type = 1
       loose_hop_flag = 0
       subobj_ip = ero_subobj[1]
       subobj_mask = ero_subobj[2]
       summarize_obj = ((loose_hop_flag << 7 ) | (subobj_type & 127))
       packed_obj = struct.pack("!BBIBB",(loose_hop_flag<< 7)|1,8,subobj_ip,subobj_mask,0)
       return (size,packed_obj)

   '''
         0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |L|    Type     |     Length    |  ST   |     Flags     |F|S|C|M|
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                              SID                              |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     //                        NAI (variable)                       //
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


        0                   1                   2                   3
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
     |                      Local IPv4 address                       |
     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


   '''



   def generate_sr_ero_subobject(self,sr_ero_subobj):
       size=12
       subobj_type =5
       loose_hop_flag = 0
       SID_TYPE = 16 #0001 0000
       M_FLAG =1
       ero_subobj = sr_ero_subobj[1] << 12
       summarize_obj = ((loose_hop_flag << 7) | (subobj_type & 127))
       packed_obj = struct.pack("!BBBBII",(loose_hop_flag<<7)|5,size,SID_TYPE,M_FLAG,ero_subobj,self.ip2int(sr_ero_subobj[0]))
       return (size,packed_obj)

   def generate_sr_ero_object(self,ero_list):
       subobj_size = 0
       packed_ero_obj = b''
       for ero_subobj in ero_list:
           packed_subobj = self.generate_sr_ero_subobject(ero_subobj)
           subobj_size += packed_subobj[0]
           packed_ero_obj = packed_ero_obj + packed_subobj[1]
       packed_common_hdr = self.generate_common_obj_hdr(7,1,subobj_size+4)
       return (subobj_size+4,packed_common_hdr + packed_ero_obj)


   def generate_ero_object(self,ero_list):
       subobj_size=0
       packed_ero_obj = b''
       for ero_subobj in ero_list:
           packed_subobj = self.generate_ero_subobject(ero_subobj)
           subobj_size += packed_subobj[0]
           packed_ero_obj = packed_ero_obj + packed_subobj[1]
       packed_common_hdr = self.generate_common_obj_hdr(7,1,subobj_size+4)
       return (subobj_size+4,packed_common_hdr + packed_ero_obj)

   def generate_bw_object(self,obj):
       bandwidth = 0
       packed_obj= struct.pack(self._bw_obj_fmt,bandwidth)
       size=4
       packed_common_hdr=self.generate_common_obj_hdr(5,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_obj)))

   def generate_pceint_bw_object(self):
       bandwidth = 10
       packed_obj = struct.pack(self._bw_obj_fmt,bandwidth)
       size = 4
       packed_common_hdr = self.generate_common_obj_hdr(5,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_obj)))

   '''
        0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Exclude-any                             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Include-any                             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                       Include-all                             |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Setup Prio   |  Holding Prio |     Flags   |L|   Reserved    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                                                               |
   //                     Optional TLVs                           //
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

                  Figure 16: LSPA Object Body Format
   '''

   def generate_lspa_obj(self,obj):
       size = 16
       setup_pri = obj[0]
       hold_pri = obj[1]
       L_flag = obj[2]
       packed_lspa_obj = struct.pack(self._lspa_obj_fmt,0,0,0,6,6,L_flag,0)
       packed_common_hdr = self.generate_common_obj_hdr(9,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_lspa_obj)))

   def generate_pceint_lspa_obj(self,LSPA_PROPERTIES):
       size = 16
       setup_pri = LSPA_PROPERTIES[0]
       hold_pri = LSPA_PROPERTIES[1]
       L_flag = LSPA_PROPERTIES[2]
       packed_lspa_obj = struct.pack(self._lspa_obj_fmt,0,0,0,setup_pri,hold_pri,L_flag,0)
       packed_common_hdr = self.generate_common_obj_hdr(9,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_lspa_obj)))

   def generate_endpoint_obj(self,source,destination):
       size = 8
       source_ip = source
       dest_ip = destination
       packed_endpoint_obj = struct.pack(self._endpoint_obj_fmt,source_ip,dest_ip)
       packed_common_hdr = self.generate_common_obj_hdr(4,1,size+4)
       return (size+4,b"".join((packed_common_hdr,packed_endpoint_obj)))

   def generate_pcep_msg(self,msg):
       print ("Generating PCEP Message")
       if msg[0] == 'lsp_update':
           return (self.generate_lsp_upd_msg(msg[1]))
       return None

   def generate_lsp_upd_msg(self,obj_list):
       size = 0
       packed_lspupd_msg =b''
       if self._srp_id < 255 :
           packed_srp_msg_obj = self.generate_srp_object(self._srp_id)
           self._srp_id+= 1
       else:
           self._srp_id =1
           packed_srp_msg_obj = self.generate_srp_object(self._srp_id)

       size += packed_srp_msg_obj[0]
       packed_lspupd_msg = b"".join((packed_lspupd_msg,packed_srp_msg_obj[1]))
       for obj in obj_list:
           print ("The Object is " , obj)
           if obj[0] == 'LSP_Object':
               packed_lsp_msg_obj = self.generate_lsp_obj(obj[1])
               size+= packed_lsp_msg_obj[0]
               packed_lspupd_msg = b"".join((packed_lspupd_msg,packed_lsp_msg_obj[1]))
           elif obj[0] == 'ERO_List':
               user_ero_list = [(1,self.ip2int('2.2.2.2'),32),(1,self.ip2int('3.3.3.3'),32),(1,self.ip2int('4.4.4.4'),32)]
               packed_ero_msg_obj = self.generate_ero_object(user_ero_list)
               size+=packed_ero_msg_obj[0]
               packed_lspupd_msg = b"".join((packed_lspupd_msg,packed_ero_msg_obj[1]))
           elif obj[0] == 'LSPA':
               packed_lspa_msg_obj = self.generate_lspa_obj(obj[1])
               size+= packed_lspa_msg_obj[0]
               packed_lspupd_msg = b"".join((packed_lspupd_msg,packed_lspa_msg_obj[1]))
           elif obj[0] == 'Bandwidth_Object':
               packed_bw_msg_obj = self.generate_bw_object(obj[1])
               size+=packed_bw_msg_obj[0]
               packed_lspupd_msg = b"".join((packed_lspupd_msg,packed_bw_msg_obj[1]))
       common_hdr = struct.pack(self._common_hdr_format,32,11,size+4)
       return b"".join((common_hdr,packed_lspupd_msg))

   def generate_sr_lsp_inititate_msg(self,ERO_LIST,TUNNEL_SRC_DST,LSPA_PROPERTIES,TUNNEL_NAME):
       size =0
       ero_ip_list = list ()
       packed_lspint_msg = b''

       if self._srp_id < 255:
           packed_srp_msg_obj = self.generate_sr_srp_object(self._srp_id)
           self._srp_id+=1
       else:
           self._srp_id =1
           packed_srp_msg_obj = self.generate_sr_srp_object(self._srp_id)
       size += packed_srp_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_srp_msg_obj[1]))

       packed_lsp_msg_obj = self.generate_pceint_lsp_obj(TUNNEL_NAME)
       size+= packed_lsp_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_lsp_msg_obj[1]))

       source = self.ip2int(TUNNEL_SRC_DST[0])
       destination = self.ip2int(TUNNEL_SRC_DST[1])
       packed_endpoint_msg_obj= self.generate_endpoint_obj(source,destination)
       size += packed_endpoint_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_endpoint_msg_obj[1]))

       packed_ero_msg_obj = self.generate_sr_ero_object(ERO_LIST)
       size+= packed_ero_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_ero_msg_obj[1]))

       packed_lspa_msg_obj = self.generate_pceint_lspa_obj(LSPA_PROPERTIES)
       size+= packed_lspa_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_lspa_msg_obj[1]))

       packed_bw_msg_obj = self.generate_pceint_bw_object()
       size+= packed_bw_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_bw_msg_obj[1]))

       common_hdr = struct.pack(self._common_hdr_format,32,12,size+4)
       return b"".join((common_hdr,packed_lspint_msg))

   def generate_lsp_inititate_msg(self,ERO_LIST,TUNNEL_SRC_DST,LSPA_PROPERTIES,TUNNEL_NAME):
       size =0
       ero_ip_list = list ()
       packed_lspint_msg = b''

       if self._srp_id < 255:
           packed_srp_msg_obj = self.generate_srp_object(self._srp_id)
           self._srp_id+=1
       else:
           self._srp_id =1
           packed_srp_msg_obj = self.generate_srp_object(self._srp_id)
       size += packed_srp_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_srp_msg_obj[1]))

       packed_lsp_msg_obj = self.generate_pceint_lsp_obj(TUNNEL_NAME)
       size+= packed_lsp_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_lsp_msg_obj[1]))

       source = self.ip2int(TUNNEL_SRC_DST[0])
       destination = self.ip2int(TUNNEL_SRC_DST[1])
       packed_endpoint_msg_obj= self.generate_endpoint_obj(source,destination)
       size += packed_endpoint_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_endpoint_msg_obj[1]))

       for ero in ERO_LIST:
           ero_ip_list.append((0,self.ip2int(ero),32))
       packed_ero_msg_obj = self.generate_ero_object(ero_ip_list)
       size+= packed_ero_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_ero_msg_obj[1]))

       packed_lspa_msg_obj = self.generate_pceint_lspa_obj(LSPA_PROPERTIES)
       size+= packed_lspa_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_lspa_msg_obj[1]))

       '''
       packed_bw_msg_obj = self.generate_pceint_bw_object()
       size+= packed_bw_msg_obj[0]
       packed_lspint_msg = b"".join((packed_lspint_msg,packed_bw_msg_obj[1]))
       '''
       common_hdr = struct.pack(self._common_hdr_format,32,12,size+4)
       return b"".join((common_hdr,packed_lspint_msg))










