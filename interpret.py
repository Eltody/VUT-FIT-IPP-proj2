# Predmet: IPP 2021
# Popis: Projekt c.2 - Interpret jazyka IPPcode21
# Nazov suboru: interpret.py
# Autor: Tomas Zatko (xzatko02)
# Datum: 21.2.2021

# nacitanie kniznic
import getopt
import sys
import xml.etree.ElementTree as ET
import re
import errno

def Main():
    if len(sys.argv) > 3:
        print("Wrong number of arguments!")
        exit(10)
    if [tmp for tmp in sys.argv if 'help' in tmp]:  # ak zadany parameter --help
        print('Skript nacita XML reprezentaciu programu a tento program s vyuzitim vstupu podla parametrov prikazovej riadky interpretuje a generuje vystup.')
        print('--help           vytiskne napovedu')
        print('--source=file    vstupny subor s XML reprezentaciou zdrojoveho kodu')
        print('--input=file     subor so vstupmi pre samotnu interpretaciu zadaneho zdrojoveho kodu')
        exit(0)
    else:   # zadanie parametrov --source a --input
        file_from_args_tmp = [tmp for tmp in sys.argv if 'source=' in tmp]  # nacitanie source=file
        read_from_args_tmp = [tmp for tmp in sys.argv if 'input=' in tmp]    # nacitanie input=file (input pre instr. read)
        if file_from_args_tmp == [] and read_from_args_tmp != []:   # ak zadany --input a nezadany --source - oddelenie nazvov suborov
            file_from_args = sys.stdin.readline()                   # nacitavam argument file zo stdin
            sys.stdout.write(file_from_args)
            read_from_args = read_from_args_tmp[0].split("=")
            read_from_args = read_from_args[1]

        elif file_from_args_tmp != [] and read_from_args_tmp == []: # ak nezadany --input a zadany --source - oddelenie nazvov suborov
            file_from_args = file_from_args_tmp[0].split("=")
            file_from_args = file_from_args[1]

        elif file_from_args_tmp == [] and read_from_args_tmp == []: # ak nezadany --input a nezadany --source
            print("Source of file must be inputted!")
            exit(10)
        elif file_from_args_tmp != [] and read_from_args_tmp != []: # pokial nastaveny --source aj --input - tak oddelenie nazvov suborov
            file_from_args = file_from_args_tmp[0].split("=")
            file_from_args = file_from_args[1]
            read_from_args = read_from_args_tmp[0].split("=")
            read_from_args = read_from_args[1]

    # nacitanie a ulozenie vstupneho suboru pouzivanim kniznice ElementTree
    try:
        tree = ET.parse(file_from_args)
        xml = tree.getroot()
    except FileNotFoundError as fnfe:
        exit(11)
    except Exception as e:
        exit(31)

	
    # inicializacia pomocnych premennych
    globalny_ramec = {}     # pre implementaciu slovniku globalnych premennych
    lokalny_ramec = []      # pre implementaciu slovniku lokalnych premennych
    docasny_ramec_definovany = 'false'    # premenna ako priznak pre pripadny presun na zasobnik ramcov TF -> LF
    docasny_ramec = {}      # docasny ramec pre ulozenie jednej premennej
    zasobnik = []           # datovy zasobnik
    datove_typy = ['int', 'bool', 'string', 'type', 'label']    # datove typy bez nil
    dict_labels = {}        # zoznam labelov
    cislo_instrukcie = 0
    inst_stack = []         # zasobnik pre instrukcie

    # inicializacia pomocnych premennych pre kontrolu syntaxe
    type = 'type'   # skuska vymazat
    mozne_typy = ['var', 'int', 'string', 'bool', 'nil', 'label', 'type']                               # vsetky datove typy
    opcode_zero_arg = ['BREAK', 'RETURN', 'CREATEFRAME', 'PUSHFRAME', 'POPFRAME']                       # vsetky instrukcie s 0 argumentami
    opcode_one_arg = ['DEFVAR', 'POPS', 'WRITE', 'DPRINT', 'PUSHS', 'EXIT', 'CALL', 'LABEL', 'JUMP']    # vsetky instrukcie s 1 argumentom
    opcode_two_arg = ['MOVE', 'STRLEN', 'INT2CHAR', 'TYPE', 'NOT', 'READ']                              # vsetky instrukcie s 2 argumentami
    opcode_three_arg = ['ADD', 'SUB', 'MUL', 'IDIV', 'LT', 'GT', 'EQ', 'AND', 'OR', 'CONCAT', 'STRI2INT', 'GETCHAR', 'SETCHAR', 'JUMPIFEQ', 'JUMPIFNEQ']    # vsetky instrukcie s 3 argumentami

    # kontrola existencie <program language="ippcode21">
    if xml.tag != 'program':
        exit(32)
    if 'language' not in xml.attrib:
        exit(32)

    # osetrenie existencie atributov
    for attrib in xml.attrib:
        if attrib not in ['language', 'name', 'description']:
            exit(32)

    if xml.attrib['language'].lower() != 'ippcode21':
        exit(32)

    cislo_pociatocnej_instrukcie = 0    # premenna pre kontrolu aktualneho a predchadzajuceho cisla instrukcie aby bolo mozne mat 1,2,4, cisla instrukcie a nie len 1,2,3
    for instrukcia in xml:      # prechadzam cez vsetky riadky instrukcii
        cislo_instrukcie = cislo_instrukcie + 1

        # kontrola nutnej znacky kazdej instrukcie
        if instrukcia.tag != 'instruction':
            exit(32)
        if 'order' not in instrukcia.attrib:
            exit(32)
        if 'opcode' not in instrukcia.attrib:
            exit(32)

        if instrukcia.attrib['order'] is None or not re.match('^[1-9][0-9]*$', instrukcia.attrib['order']): # akceptujem len cisla > 0 pre instruction order
            exit(32)
        string_to_int = int(instrukcia.attrib['order'])     # konvertujem string hodnotu 'order' do int pre kontrolu spravneho cisla instrukcii

        if cislo_pociatocnej_instrukcie >= string_to_int:   # pre duplikatne cisla instrukcii a aby sme povolili cisla instrukcii 1,2,4 a nie len 1,2,3
            exit(32)
        cislo_pociatocnej_instrukcie = string_to_int

        cislo_argumentu = 0                                 # pomocna premenna pre kontrolu cisla argumentu v xml subore
        instrukcia.attrib['opcode'] = instrukcia.attrib['opcode'].upper()          # prevod instrukcie na velke pismena, pretoze case insensitive a lepsie sa mi s tym bude pracovat

        # cyklus pre prechod vsetkymi argumentami danej instrukcie vo vyssie zacatom cykle for
        for instrukcia_argumenty in instrukcia:
            cislo_argumentu = cislo_argumentu + 1
            argument_s_cislom = 'arg'+f'{cislo_argumentu}'      # konvertujem int na string a pridavam to k 'arg' -> 'arg1'...

            # kontrola validneho cisla pri 'arg'
            if instrukcia_argumenty.tag is None or not re.match('^(arg)[1-9][0-9]*$', instrukcia_argumenty.tag):  # akceptujem len arg1 - argn
                exit(32)

            # kontrola vyskytu 'type' pri instrukcii, ktora ma argumenty
            if type not in instrukcia_argumenty.attrib:     # kontrola argumentu 'type'
                exit(32)

            # kontrola vyskytu len moznych datovych typov
            if instrukcia_argumenty.attrib['type'] not in mozne_typy:
                exit(32)

            # kontrola vyskytu len moznych instrukcii
            if instrukcia.attrib['opcode'] not in opcode_zero_arg and instrukcia.attrib['opcode'] not in opcode_one_arg and instrukcia.attrib['opcode'] not in opcode_two_arg and instrukcia.attrib['opcode'] not in opcode_three_arg:
                exit(32)


        # 0 argumentov instrukcie
        if cislo_argumentu == 0:
            if instrukcia.attrib['opcode'] not in opcode_zero_arg:  # kontrola opcode medzi instrukciami s 0 argumentami
                exit(32)

            if instrukcia.attrib['opcode'] == 'BREAK':
                print("Pozicia v kode: ", cislo_instrukcie)
                print("Pocet vykonanych instrukcii:", cislo_instrukcie - 1) # cislo_instrukcie alebo cislo_instrukcie - 1 ???
                print("Obsah ramcov: ", )
                print("Globalny ramec: ", globalny_ramec)
                print("Lokalny ramec: ", lokalny_ramec)
                print("Docasny ramec: ", docasny_ramec)
                print("Datovy zasobnik: ", zasobnik)
            elif instrukcia.attrib['opcode'] == 'CREATEFRAME':
                pass
            elif instrukcia.attrib['opcode'] == 'PUSHFRAME':
                pass
            elif instrukcia.attrib['opcode'] == 'POPFRAME':
                pass

        # 1 argument instrukcie
        elif cislo_argumentu == 1:
            if instrukcia.attrib['opcode'] in opcode_one_arg:
                if instrukcia.attrib['opcode'] == 'DEFVAR' or instrukcia.attrib['opcode'] == 'POPS':
                    if instrukcia_argumenty.tag == 'arg1':
                        check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)     # kontrola datovych typov a ich hodnot regexom
                    else:
                        exit(32)

                elif instrukcia.attrib['opcode'] == 'WRITE' or instrukcia.attrib['opcode'] == 'DPRINT' or instrukcia.attrib['opcode'] == 'PUSHS':
                    if instrukcia_argumenty.tag == 'arg1':
                        check_regex(instrukcia_argumenty, 1, 1, 1, 1, 0, 0)
                        arg1 = instrukcia_argumenty
                    else:
                        exit(32)

                elif instrukcia.attrib['opcode'] == 'LABEL' or instrukcia.attrib['opcode'] == 'CALL' or instrukcia.attrib['opcode'] == 'JUMP':
                    if instrukcia_argumenty.tag == 'arg1':
                        check_regex(instrukcia_argumenty, 0, 0, 0, 0, 1, 0)
                        arg1 = instrukcia_argumenty
                    else:
                        exit(32)

                elif instrukcia.attrib['opcode'] == 'EXIT':
                    if instrukcia_argumenty.tag == 'arg1':
                        check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                        arg1 = instrukcia_argumenty
                    else:
                        exit(32)
                    if arg1.attrib['type'] == 'var' or arg1.attrib['type'] == 'int':
                        if arg1.attrib['type'] == 'var':
                            ramec, nazov = arg1.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                            if ramec == 'GF':
                                if nazov not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                                    exit(54)
                            if globalny_ramec[nazov]['datovy_typ'] == 'int':
                                if globalny_ramec[nazov]['hodnota'] is None or not re.match('^([1-4]?[0-9]|0)$', globalny_ramec[nazov]['hodnota']):
                                    exit(57)
                                to_int_converted = int(globalny_ramec[nazov]['hodnota'])
                                exit(to_int_converted)
                            else:
                                if globalny_ramec[nazov]['hodnota'] is None:
                                    exit(56)    # chybajuca hodnota
                                else:
                                    exit(53)    # nespravny datovy typ
                        elif arg1.attrib['type'] == 'int':
                            if arg1.text is None or not re.match('^([1-4]?[0-9]|0)$', instrukcia_argumenty.text):
                                exit(57)
                            to_int_converted = int(arg1.text)
                            exit(to_int_converted)
                    else:
                        exit(53)
            else:
                exit(32)

        # 2 argumenty instrukcie
        elif cislo_argumentu == 2:
            if instrukcia.attrib['opcode'] in opcode_two_arg:
                if instrukcia.attrib['opcode'] == 'STRLEN':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 0, 1, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'MOVE':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 1, 1, 1, 0, 1)
                            arg2 = instrukcia_argumenty
                            if arg2.text is None:
                                arg2.text = ''
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'INT2CHAR':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'TYPE':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 1, 1, 1, 0, 1)
                            arg2 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'NOT':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 1, 0, 0)
                            arg2 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'READ':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.attrib['type'] != 'type':
                                exit(32)
                            arg2 = instrukcia_argumenty
                        else:
                            exit(32)
            else:
                exit(32)

        elif cislo_argumentu == 3:
            if instrukcia.attrib['opcode'] in opcode_three_arg:
                if instrukcia.attrib['opcode'] == 'ADD' or instrukcia.attrib['opcode'] == 'SUB' or instrukcia.attrib['opcode'] == 'MUL' or instrukcia.attrib['opcode'] == 'IDIV':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'LT' or instrukcia.attrib['opcode'] == 'GT' or instrukcia.attrib['opcode'] == 'EQ':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 1, 1, 1, 0, 1)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 1, 1, 1, 0, 1)
                            arg3 = instrukcia_argumenty

                elif instrukcia.attrib['opcode'] == 'AND' or instrukcia.attrib['opcode'] == 'OR':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 1, 0, 0)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 1, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'CONCAT':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 0, 1, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            if instrukcia_argumenty.text is not None:
                                check_regex(instrukcia_argumenty, 1, 0, 1, 0, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'STRI2INT':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.attrib['type'] == 'var':
                                if instrukcia_argumenty.text is None or not re.match('^(TF|LF|GF)@([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', instrukcia_argumenty.text):
                                    exit(32)
                            elif instrukcia_argumenty.attrib['type'] == 'string':
                                if instrukcia_argumenty.text == ' ':
                                    pass
                                elif instrukcia_argumenty.text is None or not re.match('^([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', instrukcia_argumenty.text):
                                    exit(32)
                            else:
                                exit(53)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'GETCHAR':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 0, 1, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'SETCHAR':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 1, 0, 0, 0, 0, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            check_regex(instrukcia_argumenty, 1, 1, 0, 0, 0, 0)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            if instrukcia_argumenty.text is None:
                                exit(58)
                            check_regex(instrukcia_argumenty, 1, 0, 1, 0, 0, 0)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)

                elif instrukcia.attrib['opcode'] == 'JUMPIFEQ' or instrukcia.attrib['opcode'] == 'JUMPIFNEQ':
                    for instrukcia_argumenty in instrukcia:  # prechadzam cez vsetky argumenty instrukcie kvoli kontrole datovych typov
                        if instrukcia_argumenty.tag == 'arg1':
                            check_regex(instrukcia_argumenty, 0, 0, 0, 0, 1, 0)
                            arg1 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg2':
                            if instrukcia_argumenty.attrib['type'] == 'var' or instrukcia_argumenty.attrib['type'] == 'int' or instrukcia_argumenty.attrib['type'] == 'string' or instrukcia_argumenty.attrib['type'] == 'bool':
                                porovnanie_typu = instrukcia_argumenty.attrib['type']
                            else:
                                exit(53)
                            arg2 = instrukcia_argumenty
                        elif instrukcia_argumenty.tag == 'arg3':
                            if instrukcia_argumenty.attrib['type'] == porovnanie_typu:
                                pass
                            else:
                                exit(53)
                            arg3 = instrukcia_argumenty
                        else:
                            exit(32)
            else:
                exit(32)
        # viac argumentov ako 3 nepodporujeme v IPPcode21
        else:
            exit(32)

########################################################################################################
# interpretacia instrukcii

        # CREATEFRAME
        if instrukcia.attrib['opcode'] == 'CREATEFRAME':
            docasny_ramec_definovany = 'true'

        # PUSHFRAME
        elif instrukcia.attrib['opcode'] == 'PUSHFRAME':
            if docasny_ramec_definovany == 'true':  # definovany
                if len(docasny_ramec) <= 0:
                    exit(54)
                TF_name = list(docasny_ramec)[0]
                TF_datovy_typ = docasny_ramec[TF_name]['datovy_typ']
                TF_hodnota = docasny_ramec[TF_name]['hodnota']
                lokalny_ramec.append(TF_datovy_typ)
                lokalny_ramec.append(TF_hodnota)
                docasny_ramec_definovany = 'false'  # po vykonani pushframe nedefinovany
                docasny_ramec = {}      # vymazanie info o jedinej TF premennej
            else:
                exit(55)    # ramec neexistuje

        # POPFRAME
        elif instrukcia.attrib['opcode'] == 'POPFRAME':
            TF_name = list(docasny_ramec)[0]    # ziskam nazov jedineho docasneho ramca
            docasny_ramec[TF_name]['datovy_typ'] = lokalny_ramec.pop(0)  # popnutie datoveho typu a ulozenie do TF
            docasny_ramec[TF_name]['hodnota'] = lokalny_ramec.pop(0) # popnutie hodnoty a ulozenie do TF

        # PUSHS
        elif instrukcia.attrib['opcode'] == 'PUSHS':
            zasobnik.append((instrukcia_argumenty.attrib['type'], instrukcia_argumenty.text))   # pushnem na zasobnik dat.typ s jeho hodnotou

        # POPS
        elif instrukcia.attrib['opcode'] == 'POPS':
            if len(zasobnik) <= 0:
                exit(56)    # prazdny zasobnik
            else:
                ramec, nazov = instrukcia_argumenty.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if ramec == 'GF':
                    data_pop = zasobnik.pop()
                    if nazov not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    globalny_ramec[nazov]['datovy_typ'] = data_pop[0]   # datovy typ z popnutej hodnoty
                    globalny_ramec[nazov]['hodnota'] = data_pop[1]      # hodnota z popnutej hodnoty

        # DEFVAR
        elif instrukcia.attrib['opcode'] == 'DEFVAR':
            ramec, nazov = instrukcia_argumenty.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
            if ramec == 'GF':
                if nazov in globalny_ramec:
                    exit(52)            # opakovana definicia premennej uz existujucej v danom ramci
                globalny_ramec[nazov] = {'datovy_typ': None, 'hodnota': None}
            elif ramec == 'TF':
                docasny_ramec[nazov] = {'datovy_typ': None, 'hodnota': None}

        # WRITE DPRINT
        elif instrukcia.attrib['opcode'] == 'WRITE' or instrukcia.attrib['opcode'] == 'DPRINT':
            if arg1.attrib['type'] == 'nil' and arg1.text == 'nil':
                pass
            elif arg1.attrib['type'] in datove_typy:      # nie je to VAR
                datovy_typ_premennej = arg1.attrib['type']
                text_premennej = arg1.text
                if instrukcia.attrib['opcode'] == 'WRITE':
                    print(text_premennej, end='')
                elif instrukcia.attrib['opcode'] == 'DPRINT':
                    print(text_premennej, file=sys.stderr)
            elif arg1.attrib['type'] == 'var':              # je to VAR
                datovy_typ_premennej, text_premennej = arg1.text.split('@', 1)
                if datovy_typ_premennej == 'GF':
                    if text_premennej not in globalny_ramec:    # pokus o citanie neexistujucej premennej
                        exit(54)
                    if globalny_ramec[text_premennej]['hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                        exit(56)
                elif datovy_typ_premennej == 'TF':
                    if text_premennej not in docasny_ramec:    # pokus o citanie neexistujucej premennej
                        exit(54)
                    if docasny_ramec[text_premennej]['hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                        exit(56)

                if instrukcia.attrib['opcode'] == 'WRITE':
                    if datovy_typ_premennej == 'GF':
                        if globalny_ramec[text_premennej]['datovy_typ'] == 'nil':
                            pass
                        if globalny_ramec[text_premennej]['hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                            print('', end='')
                        else:
                            print(globalny_ramec[text_premennej]['hodnota'], end='')  # NOT A DEBUG, end='' zamedzuje dodatocnemu odriadkovaniu

                    elif datovy_typ_premennej == 'TF':
                        if docasny_ramec[text_premennej]['datovy_typ'] == 'nil':
                            pass
                        if docasny_ramec[text_premennej]['hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                            print('', end='')
                        else:
                            print(docasny_ramec[text_premennej]['hodnota'], end='')  # NOT A DEBUG, end='' zamedzuje dodatocnemu odriadkovaniu

                    elif datovy_typ_premennej == 'LF':
                        if lokalny_ramec[0] == 'nil':
                            pass
                        if lokalny_ramec[1] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                            print('', end='')
                        else:
                            print(lokalny_ramec[1], end='')  # NOT A DEBUG, end='' zamedzuje dodatocnemu odriadkovaniu

                elif instrukcia.attrib['opcode'] == 'DPRINT':
                    if datovy_typ_premennej == 'GF':
                        if globalny_ramec[text_premennej]['datovy_typ'] == 'nil':
                            pass
                        if globalny_ramec[text_premennej][
                            'hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                            print('', file=sys.stderr)
                        else:
                            print(globalny_ramec[text_premennej]['hodnota'], file=sys.stderr)  # NOT A DEBUG, end='' zamedzuje dodatocnemu odriadkovaniu

                    elif datovy_typ_premennej == 'TF':
                        if docasny_ramec[text_premennej]['datovy_typ'] == 'nil':
                            pass
                        if docasny_ramec[text_premennej][
                            'hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                            print('', file=sys.stderr)
                        else:
                            print(docasny_ramec[text_premennej]['hodnota'], file=sys.stderr)  # NOT A DEBUG, end='' zamedzuje dodatocnemu odriadkovaniu

        # MOVE
        elif instrukcia.attrib['opcode'] == 'MOVE':
            ramec, nazov = arg1.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
            if arg2.attrib['type'] in datove_typy:      # nie je to VAR
                if ramec == 'GF':
                    if nazov not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    globalny_ramec[nazov]['datovy_typ'] = arg2.attrib['type']
                    globalny_ramec[nazov]['hodnota'] = arg2.text
                elif ramec == 'TF':
                    if nazov not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    if docasny_ramec_definovany == 'true':
                        docasny_ramec[nazov]['datovy_typ'] = arg2.attrib['type']
                        docasny_ramec[nazov]['hodnota'] = arg2.text
                    else:
                        exit(55)
            elif arg2.attrib['type'] == 'nil' and arg2.text == 'nil':
                globalny_ramec[nazov]['datovy_typ'] = arg2.attrib['type']
                globalny_ramec[nazov]['hodnota'] = arg2.text

            elif arg2.attrib['type'] == 'var':          # je to VAR
                datovy_typ_premennej, text_premennej = arg2.text.split('@', 1)
                if datovy_typ_premennej == 'GF':
                    if text_premennej not in globalny_ramec:    # pokus o citanie neexistujucej premennej
                        exit(54)
                    if globalny_ramec[text_premennej]['hodnota'] is None:  # pokus o citanie hodnoty neinicializovanej premennej
                        exit(56)
                    if ramec == 'GF':
                        if nazov not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                            exit(54)
                        globalny_ramec[nazov]['datovy_typ'] = globalny_ramec[text_premennej]['datovy_typ']
                        globalny_ramec[nazov]['hodnota'] = globalny_ramec[text_premennej]['hodnota']
                    elif ramec =='TF':
                        if nazov not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                            exit(54)
                        docasny_ramec[nazov]['datovy_typ'] = globalny_ramec[text_premennej]['datovy_typ']
                        docasny_ramec[nazov]['hodnota'] = globalny_ramec[text_premennej]['hodnota']
                elif ramec == 'TF':
                    if nazov not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    if docasny_ramec_definovany == 'true':
                        docasny_ramec[nazov]['datovy_typ'] = arg2.attrib['type']
                        docasny_ramec[nazov]['hodnota'] = arg2.text
                    else:
                        exit(55)


        # ADD SUB MUL IDIV
        elif instrukcia.attrib['opcode'] == 'ADD' or instrukcia.attrib['opcode'] == 'SUB' or instrukcia.attrib['opcode'] == 'MUL' or instrukcia.attrib['opcode'] == 'IDIV':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany,  lokalny_ramec, arg1, 'int')
            if instrukcia.attrib['opcode'] == 'ADD':
                if arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'int':
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) + int(arg3.text))  # pri probleme to vypocitat v premennej a passnut tu len premennu nie vypocet v tomto riadku

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                    globalny_ramec, nazov_arg2 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 0)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) + int(arg3.text))

                elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 0, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) + int(globalny_ramec[nazov_arg3]['hodnota'])) # str pre zapisanie cisla ako stringu do globalneho ramca

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg2, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) + int(globalny_ramec[nazov_arg3]['hodnota']))
                else:
                    exit(53)    # spatne typy operandu

            elif instrukcia.attrib['opcode'] == 'SUB':
                if arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'int':
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) - int(arg3.text))  # pri probleme to vypocitat v premennej a passnut tu len premennu nie vypocet v tomto riadku

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                    globalny_ramec, nazov_arg2 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 0)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) - int(arg3.text))

                elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 0, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) - int(globalny_ramec[nazov_arg3]['hodnota'])) # str pre zapisanie cisla ako stringu do globalneho ramca

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg2, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) - int(globalny_ramec[nazov_arg3]['hodnota']))
                else:
                    exit(53)    # spatne typy operandu

            elif instrukcia.attrib['opcode'] == 'MUL':
                if arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'int':
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) * int(arg3.text))  # pri probleme to vypocitat v premennej a passnut tu len premennu nie vypocet v tomto riadku

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                    globalny_ramec, nazov_arg2 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 0)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) * int(arg3.text))

                elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 0, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) * int(globalny_ramec[nazov_arg3]['hodnota'])) # str pre zapisanie cisla ako stringu do globalneho ramca

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg2, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 1)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) * int(globalny_ramec[nazov_arg3]['hodnota']))
                else:
                    exit(53)    # spatne typy operandu

            elif instrukcia.attrib['opcode'] == 'IDIV':
                if arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'int':
                    if arg3.text == '0':
                        exit(57)    # delenie nulou
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) // int(arg3.text))  # pri probleme to vypocitat v premennej a passnut tu len premennu nie vypocet v tomto riadku

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                    if arg3.text == '0':
                        exit(57)    # delenie nulou
                    globalny_ramec, nazov_arg2 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 0)
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) // int(arg3.text))

                elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 0, arg3, 1)
                    if globalny_ramec[nazov_arg3]['hodnota'] == '0':
                        exit(57)    # delenie nulou
                    globalny_ramec[nazov]['hodnota'] = str(int(arg2.text) // int(globalny_ramec[nazov_arg3]['hodnota'])) # str pre zapisanie cisla ako stringu do globalneho ramca

                elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                    globalny_ramec, nazov_arg2, nazov_arg3 = check_add_sub_mul_idiv(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2, 1, arg3, 1)
                    if globalny_ramec[nazov_arg3]['hodnota'] == '0':
                        exit(57)    # delenie nulou
                    globalny_ramec[nazov]['hodnota'] = str(int(globalny_ramec[nazov_arg2]['hodnota']) // int(globalny_ramec[nazov_arg3]['hodnota']))
                else:
                    exit(53)    # spatne typy operandu
        # TYPE
        elif instrukcia.attrib['opcode'] == 'TYPE':
            ramec, nazov = arg1.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
            if arg1.attrib['type'] != 'var':
                exit(53)
            if ramec == 'GF':
                if nazov not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
            elif ramec == 'TF':
                if docasny_ramec_definovany == 'false':
                    exit(55)
                if nazov not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
            elif ramec == 'LF':
                if nazov not in lokalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)

            if arg2.attrib['type'] in ['int', 'bool', 'string', 'nil']:
                globalny_ramec[nazov]['datovy_typ'] = 'string'
                globalny_ramec[nazov]['hodnota'] = arg2.attrib['type']
            elif arg2.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if ramec_arg2 == 'GF':
                    if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    if globalny_ramec[nazov_arg2]['datovy_typ'] is None:
                        globalny_ramec[nazov]['datovy_typ'] = 'string'
                        globalny_ramec[nazov]['hodnota'] = ''    # symb je neinicializovana premenna, typ bude prazdny retazec
                    else:
                        stored_arg2_data_type = globalny_ramec[nazov_arg2]['datovy_typ']
                        globalny_ramec[nazov]['datovy_typ'] = 'string'
                        globalny_ramec[nazov]['hodnota'] = stored_arg2_data_type
                elif ramec_arg2 == 'TF':
                    if docasny_ramec_definovany == 'false':
                        exit(55)
                    if nazov_arg2 not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    if docasny_ramec[nazov_arg2]['datovy_typ'] is None:
                        docasny_ramec[nazov]['datovy_typ'] = 'string'
                        docasny_ramec[nazov]['hodnota'] = ''    # symb je neinicializovana premenna, typ bude prazdny retazec
                    else:
                        stored_arg2_data_type = docasny_ramec[nazov_arg2]['datovy_typ']
                        docasny_ramec[nazov]['datovy_typ'] = 'string'
                        docasny_ramec[nazov]['hodnota'] = stored_arg2_data_type
                elif ramec_arg2 == 'LF':
                    if nazov_arg2 not in lokalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                    if lokalny_ramec[nazov_arg2]['datovy_typ'] is None:
                        lokalny_ramec[nazov]['datovy_typ'] = 'string'
                        lokalny_ramec[nazov]['hodnota'] = ''    # symb je neinicializovana premenna, typ bude prazdny retazec
                    else:
                        stored_arg2_data_type = lokalny_ramec[nazov_arg2]['datovy_typ']
                        lokalny_ramec[nazov]['datovy_typ'] = 'string'
                        lokalny_ramec[nazov]['hodnota'] = stored_arg2_data_type
            else:
                exit(53)  # spatne typy operandu

        # CONCAT
        elif instrukcia.attrib['opcode'] == 'CONCAT':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'string')

            if arg2.attrib['type'] in ['string'] and arg3.attrib['type'] in ['string']:
                if arg2.text is not None and arg3.text is not None:
                    globalny_ramec[nazov]['hodnota'] = arg2.text + arg3.text    # spojenie dvoch retazcov do jedneho
                elif arg2.text is None and arg3.text is None:
                    globalny_ramec[nazov]['hodnota'] = ''
                elif arg2.text is None:
                    globalny_ramec[nazov]['hodnota'] = arg3.text  # spojenie dvoch retazcov do jedneho
                elif arg3.text is None:
                    globalny_ramec[nazov]['hodnota'] = arg2.text  # spojenie dvoch retazcov do jedneho

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] in ['string']:
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None and globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(53) # spatne typy operandu
                if arg3.text is None:
                    globalny_ramec[nazov]['hodnota'] = globalny_ramec[nazov_arg2]['hodnota']
                elif globalny_ramec[nazov_arg2]['hodnota'] is None:
                    globalny_ramec[nazov]['hodnota'] = arg3.text
                elif globalny_ramec[nazov_arg2]['hodnota'] is not None and arg3.text is not None:
                    globalny_ramec[nazov]['hodnota'] = globalny_ramec[nazov_arg2]['hodnota'] + arg3.text

            elif arg2.attrib['type'] in ['string'] and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg3]['hodnota'] is None and globalny_ramec[nazov_arg3]['datovy_typ'] != 'string':
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'string':
                    exit(53) # spatne typy operandu
                globalny_ramec[nazov]['hodnota'] = arg3.text + globalny_ramec[nazov_arg3]['hodnota']

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(53) # spatne typy operandu
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'string':
                    exit(53) # spatne typy operandu
                globalny_ramec[nazov]['hodnota'] = globalny_ramec[nazov_arg2]['hodnota'] + globalny_ramec[nazov_arg3]['hodnota']

            else:
                exit(53) # spatne typy operandu

        # AND, OR
        elif instrukcia.attrib['opcode'] == 'AND' or instrukcia.attrib['opcode'] == 'OR':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany,  lokalny_ramec, arg1, 'bool')

            if arg2.attrib['type'] == 'bool' and arg3.attrib['type'] == 'bool':
                if instrukcia.attrib['opcode'] == 'OR':
                    if arg2.text == 'false' and arg3.text == 'false':
                        globalny_ramec[nazov]['hodnota'] = 'false'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'true'
                if instrukcia.attrib['opcode'] == 'AND':
                    if arg2.text == 'true' and arg3.text == 'true':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'bool':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'bool':
                    exit(56)  # chybajuca hodnota
                if instrukcia.attrib['opcode'] == 'OR':
                    if globalny_ramec[nazov_arg2]['hodnota'] == 'false' and arg3.text == 'false':
                        globalny_ramec[nazov]['hodnota'] = 'false'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'true'
                if instrukcia.attrib['opcode'] == 'AND':
                    if globalny_ramec[nazov_arg2]['hodnota'] == 'true' and arg3.text == 'true':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

            elif arg2.attrib['type'] == 'bool' and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'bool':
                    exit(56)  # chybajuca hodnota
                if instrukcia.attrib['opcode'] == 'OR':
                    if arg2.text == 'false' and globalny_ramec[nazov_arg3]['hodnota'] == 'false':
                        globalny_ramec[nazov]['hodnota'] = 'false'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'true'
                if instrukcia.attrib['opcode'] == 'AND':
                    if arg2.text == 'true' and globalny_ramec[nazov_arg3]['hodnota'] == 'true':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'bool':
                    exit(56)  # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'bool':
                    exit(56)  # chybajuca hodnota
                if instrukcia.attrib['opcode'] == 'OR':
                    if globalny_ramec[nazov_arg2]['hodnota'] == 'false' and globalny_ramec[nazov_arg3]['hodnota'] == 'false':
                        globalny_ramec[nazov]['hodnota'] = 'false'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'true'
                if instrukcia.attrib['opcode'] == 'AND':
                    if globalny_ramec[nazov_arg2]['hodnota'] == 'true' and globalny_ramec[nazov_arg3]['hodnota'] == 'true':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

            else:
                exit(53)

        # NOT
        elif instrukcia.attrib['opcode'] == 'NOT':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany,  lokalny_ramec, arg1, 'bool')

            if arg2.attrib['type'] == 'bool':
                if arg2.text == 'true':
                    globalny_ramec[nazov]['hodnota'] = 'false'
                else:
                    globalny_ramec[nazov]['hodnota'] = 'true'

            elif arg2.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'bool':
                    exit(53)    # nespravny typ operandu
                if globalny_ramec[nazov_arg2]['hodnota'] == 'true':
                    globalny_ramec[nazov]['hodnota'] = 'false'
                else:
                    globalny_ramec[nazov]['hodnota'] = 'true'

            else:
                exit(53)

        # LABEL
        elif instrukcia.attrib['opcode'] == 'LABEL':
            if arg1.text not in dict_labels:
                dict_labels[arg1.text] = arg1.text  # TODO VYMYSLIET AKO BUDE FUNGOVAT LABEL, TERAZ LEN UKLADAM NAZOV
            else:
                exit(52)    # pokus o vytvorenie dvoch rovnako pomenovanych navesti na roznych miestach programu

        elif instrukcia.attrib['opcode'] == 'JUMP':     # TODO DOKONCIT
            pass;
        elif instrukcia.attrib['opcode'] == 'JUMPIFEQ': # TODO DOKONCIT
            pass;
        elif instrukcia.attrib['opcode'] == 'JUMPIFNEQ':# TODO DOKONCIT
            pass;
        elif instrukcia.attrib['opcode'] == 'RETURN':   # DOKONCIT RETURN
            if inst_stack == []:    # pokial je zasobnik instrukcii prazdny - error
                exit(56)
        elif instrukcia.attrib['opcode'] == 'CALL':     # TODO DOKONCIT
            pass;

        # LT, GT, EQ
        elif instrukcia.attrib['opcode'] == 'LT' or instrukcia.attrib['opcode'] == 'GT' or instrukcia.attrib['opcode'] == 'EQ':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany,  lokalny_ramec, arg1, 'bool')
            if arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if ramec_arg2 == 'GF':
                    if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                if ramec_arg3 == 'GF':
                    if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)
                if instrukcia.attrib['opcode'] == 'EQ' and globalny_ramec[nazov_arg2]['datovy_typ'] == 'nil':
                    if globalny_ramec[nazov_arg3]['datovy_typ'] == 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'
                elif instrukcia.attrib['opcode'] == 'EQ' and globalny_ramec[nazov_arg3]['datovy_typ'] == 'nil':
                    if globalny_ramec[nazov_arg2]['datovy_typ'] == 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

                elif globalny_ramec[nazov_arg2]['datovy_typ'] == globalny_ramec[nazov_arg3]['datovy_typ']:
                    if instrukcia.attrib['opcode'] == 'EQ':
                        if globalny_ramec[nazov_arg2]['hodnota'] == globalny_ramec[nazov_arg3]['hodnota']:
                            globalny_ramec[nazov]['hodnota'] = 'true'
                        else:
                            globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'GT':
                        if globalny_ramec[nazov_arg2]['datovy_typ'] == 'int':
                            if int(globalny_ramec[nazov_arg2]['hodnota']) > int(globalny_ramec[nazov_arg3]['hodnota']):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'string':
                            if globalny_ramec[nazov_arg2]['hodnota'] > globalny_ramec[nazov_arg3]['hodnota']:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'bool':
                            if globalny_ramec[nazov_arg2]['hodnota'] == 'true' and globalny_ramec[nazov_arg3]['hodnota'] == 'false':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'LT':
                        if globalny_ramec[nazov_arg2]['datovy_typ'] == 'int':
                            if int(globalny_ramec[nazov_arg2]['hodnota']) < int(globalny_ramec[nazov_arg3]['hodnota']):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'string':
                            if globalny_ramec[nazov_arg2]['hodnota'] < globalny_ramec[nazov_arg3]['hodnota']:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'bool':
                            if globalny_ramec[nazov_arg2]['hodnota'] == 'false' and globalny_ramec[nazov_arg3]['hodnota'] == 'true':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'
                        else:
                            exit(53)
                else:
                    exit(53)

            elif arg2.attrib['type'] == 'var' and (arg3.attrib['type'] == 'int' or arg3.attrib['type'] == 'string' or arg3.attrib['type'] == 'bool' or arg3.attrib['type'] == 'nil'):
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if ramec_arg2 == 'GF':
                    if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)
                if instrukcia.attrib['opcode'] == 'EQ' and globalny_ramec[nazov_arg2]['datovy_typ'] == 'nil':
                    if arg3.attrib['type']== 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'
                elif instrukcia.attrib['opcode'] == 'EQ' and arg3.attrib['type'] == 'nil':
                    if globalny_ramec[nazov_arg2]['datovy_typ'] == 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

                elif globalny_ramec[nazov_arg2]['datovy_typ'] == arg3.attrib['type']:
                    if instrukcia.attrib['opcode'] == 'EQ':
                        if globalny_ramec[nazov_arg2]['hodnota'] == arg3.text:
                            globalny_ramec[nazov]['hodnota'] = 'true'
                        else:
                            globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'GT':
                        if globalny_ramec[nazov_arg2]['datovy_typ'] == 'int':
                            if int(globalny_ramec[nazov_arg2]['hodnota']) > int(arg3.text):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'string':
                            if globalny_ramec[nazov_arg2]['hodnota'] > arg3.text:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'bool':
                            if globalny_ramec[nazov_arg2]['hodnota'] == 'true' and arg3.text == 'false':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'LT':
                        if globalny_ramec[nazov_arg2]['datovy_typ'] == 'int':
                            if int(globalny_ramec[nazov_arg2]['hodnota']) < int(arg3.text):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'string':
                            if globalny_ramec[nazov_arg2]['hodnota'] < arg3.text:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif globalny_ramec[nazov_arg2]['datovy_typ'] == 'bool':
                            if globalny_ramec[nazov_arg2]['hodnota'] == 'false' and arg3.text == 'true':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'
                        else:
                            exit(53)
                else:
                    exit(53)


            elif (arg2.attrib['type'] == 'int' or arg2.attrib['type'] == 'string' or arg2.attrib['type'] == 'bool' or arg2.attrib['type'] == 'nil') and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if ramec_arg3 == 'GF':
                    if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                        print(globalny_ramec)
                        exit(54)
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)
                if instrukcia.attrib['opcode'] == 'EQ' and globalny_ramec[nazov_arg3]['datovy_typ'] == 'nil':
                    if arg2.attrib['type']== 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'
                elif instrukcia.attrib['opcode'] == 'EQ' and arg2.attrib['type'] == 'nil':
                    if globalny_ramec[nazov_arg3]['datovy_typ'] == 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

                elif arg2.attrib['type'] == globalny_ramec[nazov_arg3]['datovy_typ']:
                    if instrukcia.attrib['opcode'] == 'EQ':
                        if arg2.text == globalny_ramec[nazov_arg3]['hodnota']:
                            globalny_ramec[nazov]['hodnota'] = 'true'
                        else:
                            globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'GT':
                        if arg2.attrib['type'] == 'int':
                            if int(arg2.text) > int(globalny_ramec[nazov_arg3]['hodnota']):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'string':
                            if arg2.text > globalny_ramec[nazov_arg3]['hodnota']:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'bool':
                            if arg2.text == 'true' and globalny_ramec[nazov_arg3]['hodnota'] == 'false':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'LT':
                        if arg2.attrib['type'] == 'int':
                            if int(arg2.text) < int(globalny_ramec[nazov_arg3]['hodnota']):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'string':
                            if arg2.text < globalny_ramec[nazov_arg3]['hodnota']:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'bool':
                            if arg2.text == 'false' and globalny_ramec[nazov_arg3]['hodnota'] == 'true':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'
                        else:
                            exit(53)
                else:
                    exit(53)

            elif (arg2.attrib['type'] == 'int' or arg2.attrib['type'] == 'string' or arg2.attrib['type'] == 'bool' or arg2.attrib['type'] == 'nil') and (arg3.attrib['type'] == 'int' or arg3.attrib['type'] == 'string' or arg3.attrib['type'] == 'bool' or arg3.attrib['type'] == 'nil'):
                if (arg2.attrib['type'] == 'nil' or arg3.attrib['type'] == 'nil') and instrukcia.attrib['opcode'] != 'EQ':
                    exit(53)    # nespravne typy operandov
                if instrukcia.attrib['opcode'] == 'EQ' and arg3.attrib['type'] == 'nil':
                    if arg2.attrib['type']== 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'
                elif instrukcia.attrib['opcode'] == 'EQ' and arg2.attrib['type'] == 'nil':
                    if arg3.attrib['type'] == 'nil':
                        globalny_ramec[nazov]['hodnota'] = 'true'
                    else:
                        globalny_ramec[nazov]['hodnota'] = 'false'

                elif arg2.attrib['type'] == arg3.attrib['type']:
                    if instrukcia.attrib['opcode'] == 'EQ':
                        if arg2.text == arg3.text:
                            globalny_ramec[nazov]['hodnota'] = 'true'
                        else:
                            globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'GT':
                        if arg2.attrib['type'] == 'int':
                            if int(arg2.text) > int(arg3.text):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'string':
                            if arg3.text is None:
                                arg3.text = ''
                            if arg2.text > arg3.text:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'bool':
                            if arg2.text == 'true' and arg3.text == 'false':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                    elif instrukcia.attrib['opcode'] == 'LT':
                        if arg2.attrib['type'] == 'int':
                            if int(arg2.text) < int(arg3.text):
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'string':
                            if arg3.text is None:
                                arg3.text = ''
                            if arg2.text < arg3.text:
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'

                        elif arg2.attrib['type'] == 'bool':
                            if arg2.text == 'false' and arg3.text == 'true':
                                globalny_ramec[nazov]['hodnota'] = 'true'
                            else:
                                globalny_ramec[nazov]['hodnota'] = 'false'
                        else:
                            exit(53)
                else:
                    exit(53)

            else:
                exit(53)



        # STRLEN
        elif instrukcia.attrib['opcode'] == 'STRLEN':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'int')
            if arg2.attrib['type'] == 'string':
                if arg2.text is None:
                    globalny_ramec[nazov]['hodnota'] = 0
                else:
                    globalny_ramec[nazov]['hodnota'] = len(arg2.text)   # nemalo by byt ukladanie do dictu v uvodzovkach - teda ze to je string

            elif arg2.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(53)    # nespravny typ operandu

                globalny_ramec[nazov]['hodnota'] = len(globalny_ramec[nazov_arg2]['hodnota'])
            else:
                exit(53)

        # GETCHAR
        elif instrukcia.attrib['opcode'] == 'GETCHAR':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'string')

            if arg2.attrib['type'] == 'string' and arg3.attrib['type'] == 'int':
                if int(arg3.text) < 0:
                    exit(58)    # indexacia mimo dany retazec
                if int(arg3.text) <= len(arg2.text) - 1: # lebo indexacia od zacina od nuly
                    globalny_ramec[nazov]['hodnota'] = arg2.text[int(arg3.text)] # alebo to dat do samostatnej premennej a tu passnut
                else:
                    exit(58)    # indexacia mimo dany retazec

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                globalny_ramec[nazov]['datovy_typ'] = 'string'
                arg2_gf = globalny_ramec[nazov_arg2]['hodnota']
                globalny_ramec[nazov]['hodnota'] = arg2_gf[int(arg3.text)]

            elif arg2.attrib['type'] == 'string' and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                globalny_ramec[nazov]['datovy_typ'] = 'string'
                arg3_gf = int(arg3.text)
                arg2_gf = globalny_ramec[nazov_arg2]['hodnota']
                globalny_ramec[nazov]['hodnota'] = arg2_gf[arg3_gf]

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                # TODO VSADE DOPLNIT PODMIENKU IF VAR(NA MIESTE <SYMB>) IS NONE TAK ERROR....
                globalny_ramec[nazov]['datovy_typ'] = 'string'
                arg3_gf = globalny_ramec[nazov_arg3]['hodnota']
                arg3_gf_int = int(arg3_gf)
                arg2_gf = globalny_ramec[nazov_arg2]['hodnota']
                globalny_ramec[nazov]['hodnota'] = arg2_gf[arg3_gf_int]

            else:
                exit(53)

        # INT2CHAR
        elif instrukcia.attrib['opcode'] == 'INT2CHAR':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'string')
            if arg2.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'int':
                    exit(53)    # nespravny typ operandu
                unicode_value = chr(int(globalny_ramec[nazov_arg2]['hodnota'])) # prevedenie intu na unicode znak /32 je medzera
            elif arg2.attrib['type'] == 'int':

                if int(arg2.text) < 0 or int(arg2.text) > 1114111:
                    exit(58)    # nevalidna hodnota znaku unicode
                unicode_value = chr(int(arg2.text))  # prevedenie intu na unicode znak /32 je medzera
            else:
                exit(53)
            globalny_ramec[nazov]['hodnota'] = unicode_value

        # STRI2INT
        elif instrukcia.attrib['opcode'] == 'STRI2INT':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'int')
            if arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                index_value = int(globalny_ramec[nazov_arg3]['hodnota'])
                if index_value >= 0 and index_value <= len(globalny_ramec[nazov_arg2]['hodnota']) - 1:   # index je v poriadku
                    ord_value = ord(globalny_ramec[nazov_arg2]['hodnota'][index_value])
                    globalny_ramec[nazov]['hodnota'] = ord_value
                else:
                    exit(58)    # indexacia mimo dany retazec

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'int':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg2 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                index_value = int(arg3.text)
                if index_value >= 0 and index_value <= len(globalny_ramec[nazov_arg2]['hodnota']) - 1:  # index je v poriadku
                    ord_value = ord(globalny_ramec[nazov_arg2]['hodnota'][index_value])
                    globalny_ramec[nazov]['hodnota'] = ord_value
                else:
                    exit(58)    # indexacia mimo dany retazec

            elif arg2.attrib['type'] == 'string' and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if nazov_arg3 not in globalny_ramec:  # pokus o citanie neexistujucej premennej
                    exit(54)
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                index_value = int(globalny_ramec[nazov_arg3]['hodnota'])
                if index_value >= 0 and index_value <= len(arg2.text) - 1:  # index je v poriadku
                    ord_value = ord(arg2.text[index_value])
                    globalny_ramec[nazov]['hodnota'] = ord_value
                else:
                    exit(58)    # indexacia mimo dany retazec

            elif arg2.attrib['type'] == 'string' and arg3.attrib['type'] == 'int':
                index_value = int(arg3.text)
                if index_value >= 0 and index_value <= len(arg2.text) - 1:  # index je v poriadku
                    ord_value = ord(arg2.text[index_value])
                    globalny_ramec[nazov]['hodnota'] = ord_value
                else:
                    exit(58)    # indexacia mimo dany retazec
            else:
                exit(53)

        # SETCHAR
        elif instrukcia.attrib['opcode'] == 'SETCHAR':
            if arg1.attrib['type'] == 'var':
                ramec_tmp, nazov_tmp = arg1.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if globalny_ramec[nazov_tmp]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_tmp]['datovy_typ'] != 'string':
                    exit(53)
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, 'string')
            if arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'var':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)  # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(53)
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'string':
                    exit(53)
                if globalny_ramec[nazov]['datovy_typ'] == 'string' and globalny_ramec[nazov_arg2]['datovy_typ'] == 'int' and globalny_ramec[nazov_arg3]['datovy_typ'] == 'string':
                    index_value = int(globalny_ramec[nazov_arg2]['hodnota'])
                    if globalny_ramec[nazov_arg3]['hodnota'] == '' or index_value >= 0 and index_value <= len(globalny_ramec[nazov]['hodnota']) - 1:
                        letter_list_of_var = list(globalny_ramec[nazov]['hodnota'])
                        letter_list_of_var[index_value] = globalny_ramec[nazov_arg3]['hodnota'][0]
                        globalny_ramec[nazov]['hodnota'] = ''.join(letter_list_of_var)
                    else:
                        exit(58)
                else:
                    exit(53)

            elif arg2.attrib['type'] == 'var' and arg3.attrib['type'] == 'string':
                ramec_arg2, nazov_arg2 = arg2.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if globalny_ramec[nazov_arg2]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg2]['datovy_typ'] != 'string':
                    exit(53)
                if globalny_ramec[nazov]['datovy_typ'] == 'string' and globalny_ramec[nazov_arg2]['datovy_typ'] == 'int' and arg3.attrib['type'] == 'string':
                    index_value = int(globalny_ramec[nazov_arg2]['hodnota'])
                    if arg3.text == '' or index_value >= 0 and index_value <= len(globalny_ramec[nazov]['hodnota']) - 1:
                        letter_list_of_var = list(globalny_ramec[nazov]['hodnota'])
                        letter_list_of_var[index_value] = arg3.text[0]
                        globalny_ramec[nazov]['hodnota'] = ''.join(letter_list_of_var)
                    else:
                        exit(58)
                else:
                    exit(53)

            elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'var':
                ramec_arg3, nazov_arg3 = arg3.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
                if globalny_ramec[nazov_arg3]['hodnota'] is None:
                    exit(56)    # chybajuca hodnota
                if globalny_ramec[nazov_arg3]['datovy_typ'] != 'string':
                    exit(53)
                if globalny_ramec[nazov]['datovy_typ'] == 'string' and arg2.attrib['type'] == 'int' and globalny_ramec[nazov_arg3]['datovy_typ'] == 'string':
                    index_value = int(arg2.text)
                    if globalny_ramec[nazov_arg3]['hodnota'] == '' or index_value >= 0 and index_value <= len(globalny_ramec[nazov]['hodnota']) - 1:
                        letter_list_of_var = list(globalny_ramec[nazov]['hodnota'])
                        letter_list_of_var[index_value] = globalny_ramec[nazov_arg3]['hodnota'][0]
                        globalny_ramec[nazov]['hodnota'] = ''.join(letter_list_of_var)
                    else:
                        exit(58)
                else:
                    exit(53)

            elif arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'string':
                if globalny_ramec[nazov]['datovy_typ'] == 'string' and arg2.attrib['type'] == 'int' and arg3.attrib['type'] == 'string':
                    index_value = int(arg2.text)
                    if arg3.text == '' or index_value >= 0 and index_value <= len(globalny_ramec[nazov]['hodnota']) - 1:
                        letter_list_of_var = list(globalny_ramec[nazov]['hodnota'])
                        letter_list_of_var[index_value] = arg3.text[0]
                        globalny_ramec[nazov]['hodnota'] = ''.join(letter_list_of_var)
                    else:
                        exit(58)
                else:
                    exit(53)

            else:
                exit(53)

        # READ
        elif instrukcia.attrib['opcode'] == 'READ':
            globalny_ramec, nazov = check_arg1_var_set_data_type(globalny_ramec, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1, '')
            if read_from_args_tmp == '[]':
                f = open(read_from_args, "r")
                input_from_user = f.readline()
            else:
                try:
                    input_from_user = input()
                except Exception:
                    input_from_user = ''

            if arg2.text == 'int':

                if input_from_user is None or not re.match('^([+-]?[1-9][0-9]*|[+-]?[0-9])$', input_from_user):
                    globalny_ramec[nazov]['datovy_typ'] = 'nil'
                    globalny_ramec[nazov]['hodnota'] = 'nil'
                else:
                    globalny_ramec[nazov]['datovy_typ'] = 'int'
                    globalny_ramec[nazov]['hodnota'] = input_from_user

            elif arg2.text == 'string':
                if input_from_user is None or not re.match('^([a-zA-Z]|!|\?|%|\*|\$|_| |-)( |!|\?|%|\*|\$|_|-|[\w])*$', input_from_user):
                    globalny_ramec[nazov]['datovy_typ'] = 'nil'
                    globalny_ramec[nazov]['hodnota'] = 'nil'
                else:
                    globalny_ramec[nazov]['datovy_typ'] = 'string'
                    globalny_ramec[nazov]['hodnota'] = input_from_user

            elif arg2.text == 'bool':
                input_from_user = input_from_user.lower()
                if input_from_user == 'true':
                    input_from_user = 'true'
                else:
                    input_from_user = 'false'  # chybny vstup je vzdy false
                    globalny_ramec[nazov]['datovy_typ'] = 'bool'
                    globalny_ramec[nazov]['hodnota'] = input_from_user
            else:
                exit(53)

# funkcia skontroluje regexom povolene datove typy predavane pomocou parametrov funkcie
def check_regex(instrukcia_argumenty, var, int_dt, string, bool, label, nil):
    if instrukcia_argumenty.attrib['type'] == 'var' and var == 1:
        if instrukcia_argumenty.text is None or not re.match('^(TF|LF|GF)@([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', instrukcia_argumenty.text):
            exit(32)
    elif instrukcia_argumenty.attrib['type'] == 'int' and int_dt == 1:
        if instrukcia_argumenty.text is None or not re.match('^([+-]?[1-9][0-9]*|[+-]?[0-9])$', instrukcia_argumenty.text):
            exit(32)
    elif instrukcia_argumenty.attrib['type'] == 'string' and string == 1:
        if instrukcia_argumenty.text is None:
            pass
        elif instrukcia_argumenty.text is None or not re.match('^([a-zA-Z]|!|\?|%|\*|\$|_|\\\\|-|)(!|\?|%|\*|\$|_|-|\\\\|[\w])*$', instrukcia_argumenty.text):
            exit(32)
        # v stringu hladam escape sekvenciu, tu prevediem na int a nasledne na char
        instrukcia_argumenty.text = re.sub(r'\\([0-9]{3})', lambda x: chr(int(x.group(1))), instrukcia_argumenty.text)
    elif instrukcia_argumenty.attrib['type'] == 'bool' and bool == 1:
        if instrukcia_argumenty.text is None or not re.match('^(false|true)$', instrukcia_argumenty.text):
            exit(32)
    elif instrukcia_argumenty.attrib['type'] == 'label' and label == 1:
        if instrukcia_argumenty.text is None or not re.match('^([a-zA-Z]|!|\?|%|\*|\$|_|-)(!|\?|%|\*|\$|_|-|[\w])*$', instrukcia_argumenty.text):
            exit(32)
    elif instrukcia_argumenty.attrib['type'] == 'nil' and nil == 1:
        if instrukcia_argumenty.text is None or not re.match('^(nil)*$', instrukcia_argumenty.text):
            exit(32)
    else:
        exit(53)	# nespravne typy operandov
    return



# funkcia skontroluje prvy argument <var>, nastavi jeho koncovy datovy typ
def check_arg1_var_set_data_type(global_frame, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg1_var, data_typ):
    ramec, nazov = arg1_var.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
    if arg1_var.attrib['type'] != 'var':
        exit(53)
    if ramec == 'GF':
        if nazov not in global_frame:  # pokus o citanie neexistujucej premennej
            exit(54)
        global_frame[nazov]['datovy_typ'] = data_typ
    elif ramec == 'TF':
        if docasny_ramec_definovany == 'false':
            exit(55)
        if nazov not in docasny_ramec:  # pokus o citanie neexistujucej premennej
            exit(54)
        if docasny_ramec_definovany == 'true':
            docasny_ramec[nazov]['datovy_typ'] = data_typ
    elif ramec == 'LF':
        if nazov not in lokalny_ramec:  # nedefinovana premenna
            exit(55)
        else:
            exit(54)
    return (global_frame, nazov)



# funkcia kontroluje a spracovava argumenty instrukcii ADD, SUB, MUL a IDIV
def check_add_sub_mul_idiv(global_frame, docasny_ramec, docasny_ramec_definovany, lokalny_ramec, arg2_var, bool_arg2, arg3_var, bool_arg3):
    if bool_arg2 == 1:
        ramec_arg2, nazov_arg2 = arg2_var.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
        if ramec_arg2 == 'GF':
            if nazov_arg2 not in global_frame:  # pokus o citanie neexistujucej premennej
                exit(54)
            if global_frame[nazov_arg2]['hodnota'] is None:
                exit(56)  # chybajuca hodnota
            if bool_arg3 == 0:
                return (global_frame, nazov_arg2)
        elif ramec_arg2 == 'TF':
            if docasny_ramec_definovany == 'false':
                exit(55)
            if nazov_arg2 not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                exit(54)
            if docasny_ramec[nazov_arg2]['hodnota'] is None:
                exit(56)  # chybajuca hodnota
            if bool_arg3 == 0:
                return (docasny_ramec, nazov_arg2)
        elif ramec_arg2 == 'LF':
            if nazov_arg2 not in lokalny_ramec:  # nedefinovana premenna
                exit(55)
            if bool_arg3 == 0:
                return (lokalny_ramec, nazov_arg2)

    if bool_arg3 == 1:
        ramec_arg3, nazov_arg3 = arg3_var.text.split('@', 1)  # splitnem premennu podla @ na ramec a nazov
        if ramec_arg3 == 'GF':
            if nazov_arg3 not in global_frame:  # pokus o citanie neexistujucej premennej
                exit(54)
            if global_frame[nazov_arg3]['hodnota'] is None:
                exit(56)  # chybajuca hodnota
            if bool_arg2 == 0:
                return (global_frame, nazov_arg3)
        elif ramec_arg3 == 'TF':
            if docasny_ramec_definovany == 'false':
                exit(55)
            if nazov_arg3 not in docasny_ramec:  # pokus o citanie neexistujucej premennej
                exit(54)
            if docasny_ramec[nazov_arg3]['hodnota'] is None:
                exit(56)  # chybajuca hodnota
            if bool_arg3 == 0:
               return (docasny_ramec, nazov_arg3)
        elif ramec_arg3 == 'LF':
            if nazov_arg3 not in lokalny_ramec:  # nedefinovana premenna
                exit(55)
            if bool_arg3 == 0:
                return (lokalny_ramec, nazov_arg3)

    return (global_frame, nazov_arg2, nazov_arg3)

# zavolanie fce Main
Main()