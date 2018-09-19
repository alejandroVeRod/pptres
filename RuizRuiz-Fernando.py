#!/usr/bin/python3
# coding: utf-8 
# encoding: utf-8

from socket import *

import sys
import struct
import time

UCLM_SERVER = 'atclab.esi.uclm.es'
UCLM_SERVER_PORT = 2000
MY_UDP_PORT = 2000

#   MÉTODOS AUXILIARES  #

def arreglarEcuacion(ecuacion):
    ecuacion = ecuacion.replace("[","(")
    ecuacion = ecuacion.replace("]",")")
    ecuacion = ecuacion.replace("{","(")
    ecuacion = ecuacion.replace("}",")")
    ecuacion = ecuacion.replace(" ", "")

    return ecuacion

def ecuacionBalanceada(ecuacion):
    abre = 0
    cierra = 0
    for i in ecuacion:
        if i == "(":
            abre= abre + 1
        if i == ")":
            cierra= cierra + 1
    if abre == cierra:
        return True
    else:
        return False

def resolverEcuacion(ecuacion):
    operador = ""
    resOp = 0
    subEc = ""
    iteraciones = ecuacion.count("(")
    op = ["+","-","*","/"]
    
    for i in range(0, iteraciones):
        flag1=0
        flag2=0
        flag3=0
        flag4=0
        for i in ecuacion:
            flag2=flag2+1
            if i == ")":
                flag1=flag2         
                while flag1>0:
                    flag1=flag1-1
                    if ecuacion[flag1] == "(":
                        subEc=ecuacion[flag1:flag2]
                        break
                break
        for i in subEc:
            if i == ")":
                flag4=flag3
                while flag4>0:
                    flag4=flag4-1
                    if subEc[flag4] in op:
                        if subEc[flag4-1] in op:
                            flag4=flag4-1
                            operador=subEc[flag4]
                                      
                        derecha = int(subEc[flag4+1:flag3])
                        izquierda = int(subEc[1:flag4])
                        operador=subEc[flag4]
                        flag4=0
                        
                        if operador == "+":
                            resOp=izquierda+derecha
                        if operador == "-":
                            resOp=izquierda-derecha
                        if operador == "*":
                            resOp=izquierda*derecha                        
                        if operador == "/":
                            resOp=izquierda//derecha
            flag3=flag3+1
        ecuacion=ecuacion.replace(subEc,str(resOp))
    return ecuacion

def enviarResultado(resultado, cliente, port):
    code = "("+str(resultado)+")"
    cliente.sendto(code.encode(), ((UCLM_SERVER, int(port))))
    msg, data = cliente.recvfrom(1024)
    return msg.decode()

#Codigo facilitado por los profesores modificado
def cksum(data):

    def sum16(data):
        "sum all the the 16-bit words in data"
        if len(data) % 2:
            data += '\0'.encode()

        return sum(struct.unpack("!%sH" % (len(data) // 2), data))

    retval = sum16(data)                       # sum
    retval = sum16(struct.pack('!L', retval))  # one's complement sum
    retval = (retval & 0xFFFF) ^ 0xFFFF        # one's complement
    return retval

#   MÉTODOS PRINCIPALES #

def etapa_cero():
    cliente = socket(AF_INET, SOCK_STREAM)
    cliente.connect((UCLM_SERVER, UCLM_SERVER_PORT))
    msg, data = cliente.recvfrom(1024)
    print(msg.decode())
    cliente.close()
    return msg.decode()[0:5]

def etapa_uno(ide):
    cliente = socket(AF_INET, SOCK_DGRAM)
    code = ide+" "+str(MY_UDP_PORT)
    cliente.bind(('',UCLM_SERVER_PORT))
    cliente.sendto(code.encode(), ((UCLM_SERVER, UCLM_SERVER_PORT)))
    msg, data = cliente.recvfrom(1024)
    print(msg.decode())
    cliente.close()
    return int(msg.decode()[0:4])

def etapa_dos(port):
    cliente = socket(AF_INET, SOCK_STREAM)
    cliente.connect((UCLM_SERVER, int(port)))
    msg, data = cliente.recvfrom(1024)
    ecuacion = msg.decode()
    
    while 1:

        if ecuacion[0]=="(" or ecuacion[0] == "{" or ecuacion[0] == "[":
            ecuacion = arreglarEcuacion(ecuacion)

            if ecuacionBalanceada(ecuacion) == False:
                msgs, data= cliente.recvfrom(1024)
                ecuacionsegunda = msgs.decode()
                ecuacionsegunda = arreglarEcuacion(ecuacionsegunda)
                ecuacion = ecuacion + ecuacionsegunda

            print("Esta es la ecuación a resolver: "+ str(ecuacion))
            resultado = resolverEcuacion(ecuacion)
            print(" Resultado: " + str(int(resultado)))

            ecuacion = enviarResultado(int(resultado), cliente, port)
        else:
            return ecuacion[0:5]
            break
            

    client.close()

def etapa_tres(pagina):
	#https://stackoverflow.com/questions/34192093/python-socket-get
    cliente = socket(AF_INET, SOCK_STREAM)
    cliente.connect((UCLM_SERVER, 5000))
    request="GET /"+str(pagina)+" HTTP/1.1\nHost: atclab.esi.uclm.es\n\n"
    cliente.send(request.encode())
    cliente.recv(1024)
    msg = cliente.recv(4096)	
    mensaje = msg.decode()
    print(mensaje[115:])
    return str(mensaje[115:120])
def etapa_cuatro(codigo):
    cliente = socket(AF_INET, SOCK_RAW, getprotobyname('icmp'))

    cabecera = struct.pack('!bbHhh', 8, 0, 0, 2018, 0)

    packtime = struct.pack("!d", time.time())
    packcode = codigo.encode('UTF-8')+b"\n"

    cheksum = cksum(cabecera+packtime+packcode)

    cabeza = struct.pack('!bbHhh', 8, 0, cheksum, 2018, 0)
    paquete = cabeza+packtime+packcode
    cliente.sendto(paquete, (UCLM_SERVER, UCLM_SERVER_PORT))

    msg = cliente.recv(1024)
    msg2 = (cliente.recv(2048)[36:]).decode()

    print(msg2)
    cliente.close()
    return msg2[1124:1129]

def main():
    ide=etapa_cero()
    port=etapa_uno(ide)
    pagina=etapa_dos(port)
    codigo = etapa_tres(pagina)
    ident = etapa_cuatro(codigo)
main()
