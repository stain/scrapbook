from __future__ import generators

# This is 'kid', a python module that calculates and verifies kid
# numbers on norwegian invoices. 
#
# Copyright (C) 2003 Ove Gram Nipen <ove@nipen.no>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307,
# USA.

def enkeltsiffer(produkter): 
    """Returnerer ett og ett siffer i et array av produkter"""
    for element in produkter:
        sifre = [int(siffer) for siffer in str(element)]
        
        for siffer in sifre: 
            yield siffer
    
def modulus10(fakturanr):
    """Returnerer kontrollsiffer for fakturanr regnet ut etter metoden
    Modulus 10 beskrevet i Brukerhåndbok OCRGiro Systemspesifikasjon,
    som kan legges til på slutten av fakturanr for å få en gyldig KID.
    
    Fakturanr må være en streng, siden ledende 0 er tillatt"""
    
    fakturanr = [int(element) for element in str(fakturanr)]
    lengde = len(fakturanr)

    #print "Fakturanr:", fakturanr
    #print "Lengde:", lengde

    vekttall = [0] * lengde
    produkter = [0] * lengde

    odde = 1 
    for i in range(lengde -1, 0 - 1, -1): 
        if(odde):
            vekttall[i] = 2
            odde = 0
        else:
            vekttall[i] = 1
            odde = 1

    #print "Vekttall:", vekttall
    for i in range(lengde): 
        produkter[i] = fakturanr[i] * vekttall[i]


    #print "Produkter:", produkter
    
    siffersum = 0
    for siffer in enkeltsiffer(produkter):
        siffersum += siffer
    
    siffersum = [int(element) for element in str(siffersum)]
    #print "Siffersum:", siffersum

    entallssiffer = siffersum[-1]
    
    if entallssiffer == 0:
        return "0"
    
    return str(10 - entallssiffer) 

def modulus11(fakturanr):
    """Regner ut kontrollsiffer for fakturanr vha modulus11-metoden.
    Fakturanr må være en streng, fordi ledende 0 er tillatt"""

    fakturanr = [int(element) for element in str(fakturanr)]
    lengde = len(fakturanr)

    vekttallssifre = [2,3,4,5,6,7]
    siffer = 0

    vekttall = [0] * lengde
    produkter = [0] * lengde
    
    for i in range(lengde - 1, 0 - 1, -1): 
        vekttall[i] = vekttallssifre[siffer]
        siffer = (siffer + 1) % 6 

    for i in range(lengde):
        produkter[i] = vekttall[i] * fakturanr[i]

    sum = 0
    for tall in produkter:
        sum += tall

    rest = sum % 11
    
    if(rest == 0):
        kontrollsiffer = "0"
    elif(rest == 10): 
        kontrollsiffer = "-"
    else: 
        kontrollsiffer = str(11 - rest)
   
    return kontrollsiffer
    
def verifiser(kid):
    """Verifiserer at oppgitt kid har korrekt sjekksiffer. kid må være en
    streng."""

    lengde = len(kid)

    fakturanr = kid[:-1]
    sjekksiffer = kid[-1]

    #print "Fakturanr:", fakturanr
    #print "Sjekksiffer:", sjekksiffer
    #print "Modulus10:",modulus10(fakturanr)

    return sjekksiffer == modulus10(fakturanr) \
    or sjekksiffer == modulus11(fakturanr)

def lag_kid(fakturanr):
    """Returnerer en streng som består av fakturanr + kontrollsiffer,
    som da er en gyldig KID regnet ut med modulus10"""

    return fakturanr + modulus10(fakturanr)

