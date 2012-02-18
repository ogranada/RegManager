#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Copyright (c) 2012, Oscar Granada
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. All advertising materials mentioning features or use of this software
   must display the following acknowledgement:
   This product includes software developed by the University of 
   California, Berkeley and its contributors.
4. Neither the name of the University nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""



import subprocess as sp
import StringIO
import sys, os, tempfile



class RegisterManager(object):

    BASENAMES = {
            "HKLM":"HKEY_LOCAL_MACHINE",
            "HKCU":"HKEY_CURRENT_USER",
            "HKCC":"HKEY_CURRENT_CONFIG",
            "HKCR":"HKEY_CLASSES_ROOT",
            "HKU":"HKEY_USERS"
        }

    def __init__(self,dbg=False):
        self.__debug = dbg
        self.__olderr = sys.stderr
        sys.stderr = tempfile.TemporaryFile()
        
    def __cast(self, data):
        if data[0]=="REG_BINARY":
            return int(data[1],2)
        elif data[0]=="REG_SZ" or data[0]=="REG_EXPAND_SZ":
            return data[1]
        elif data[0]=="REG_DWORD" or data[0]=="REG_QWORD":
            return int(data[1],16)
        elif data[0]=="REG_MULTI_SZ":
            return data[1].replace("\\0","\n")
    
    def __cast_val(self, data):
        if data[0]=="REG_BINARY":
            return data[0],bin(data[1])[2:]
        elif data[0]=="REG_SZ" or data[0]=="REG_EXPAND_SZ":
            return data[0],str(data[1])
        elif data[0]=="REG_DWORD" or data[0]=="REG_QWORD":
            return data[0],hex(data[1])
        elif data[0]=="REG_MULTI_SZ":
            return data[0],str(data[1]).replace("\n","\\0")
    
    def __type_and_val(self, obj):
        if type(obj) == type(0):
            return ("REG_DWORD",hex(obj))
        elif type(obj) == type(""):
            if "\n" in obj:
                return ("REG_MULTI_SZ",obj.replace("\n","\\0"))
            else:
                return ("REG_SZ",obj)
            
    
    def query(self,BRANCH="HKLM"):
        for k in self.BASENAMES.keys():
            if k in BRANCH:
                BRANCH = BRANCH.replace(k,self.BASENAMES[k])
                break
        try:
            self.__lst = ["REG","QUERY",BRANCH]
            val = sp.check_output(self.__lst,stderr=sys.stderr,shell=True)
            val = val.replace('\r','')
            val = val.replace('\n    ','\n\t')
            val = val.split('\n')
            data = {}
            subregs = []
            for line in val:
                if line.startswith("\t"):
                    ln = line.replace("\t",'').split("    ")
                    nm = ln[0] if (ln[0].lower()!='(predeterminado)' and ln[0].lower()!='(standard)') else ""
                    data[nm] = self.__cast(ln[1:])
                else:
                    if line!="" and line!=BRANCH:
                        subregs.append(line)
            data["[subregisters]"]=subregs
            return data
        except Exception, val:
            if self.__debug:
                print val
            return Exception

    def add(self, BRANCH, data={}):
        """
        pone dentro de la rama BRANCH
        los datos de data.
        data es un diccionario
        debe tener como claves
        los nombres de las claves
        del registro de windows.
        Los valores asociados a las claves
        son enteros, cadenas o tuplas,
        en el ultimo caso la posicion cero (0)
        
        la clave "[subregisters]"
        es una lista con diccionarios de subclaves.
        la clave por defecto es la que pertenece a 
        la llave vacia o ""
        """
        for k in self.BASENAMES.keys():
            if k in BRANCH:
                BRANCH = BRANCH.replace(k,self.BASENAMES[k])
                break
        
        if len(data.keys())>0:
            for k in data.keys():
                ORD = "REG ADD ".split()+[BRANCH]
                if k == "":
                    ORD.append("/ve")
                    ORD.append("/f")
                    ORD.append("/d")
                    ORD.append(data[""])
                else:
                    t_d=None
                    if type(data[k])!=type(tuple()):
                        t_d = self.__type_and_val(data[k])                    
                    else:
                        t_d = self.__cast_val(data[k])
                    ORD.append("/v")
                    ORD.append(k)
                    ORD.append("/t")
                    ORD.append(t_d[0])
                    ORD.append("/f")
                    ORD.append("/d")
                    ORD.append(t_d[1])
                ORD = [str(x) for x in ORD]
                print ' '.join(ORD)
                sp.call(ORD,stderr=sys.stderr,shell=True)
        else:
            val = "REG ADD /f".split()+[BRANCH]
            print ' '.join(val)
            sp.call(val,stderr=sys.stderr,shell=True)
            



if __name__=="__main__":
    #reg = RegisterManager(True)
    reg = RegisterManager()
    from pprint import pprint as Print
    #Print(reg.query(BRANCH = "HKLM\\Software\\Creative"))
    #Print(reg.query(BRANCH = "HKLM\\Software\\ArgoUML"))
    #Print(reg.query(BRANCH = "HKU"))
    
    reg.add("HKLM\\Software\\ArgoUML\\XXX")
    reg.add("HKLM\\Software\\ArgoUML\\XXX",{'':1,"bin_val":("REG_BINARY",720), "other_val":"Hola\nMundo"})
    
    raw_input("Enter To Continue...")
    
    
