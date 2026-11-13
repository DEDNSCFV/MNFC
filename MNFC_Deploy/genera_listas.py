import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, Protection

PASSWORD = "Isa0502"
OUTDIR = "listas_07_11_2026"
os.makedirs(OUTDIR, exist_ok=True)

LISTAS = []

LISTAS.append({"archivo": "TERE_regular_07-11-2026.xlsx", "detal": "TERE", "lista": "REGULAR",
 "quiebres": {"ROS37536", "2346"},
 "rows": [
    (1,"R-263","Caja parchos 100x195mm","Pareto"),
    (2,"VK76","Tubo escape Horse 2","Pareto"),
    (3,"MOTUL-01","Aceite 15W40 Motul 4100","Pareto"),
    (4,"EG-87.881.2.DM","Casco Phoenix verde M","Pareto"),
    (5,"TS970-1208016HG","Caucho 120/80-16 Timsum","Pareto"),
    (6,"R-262","Caja parchos 130mm","Pareto"),
    (7,"MO-139","Cigueñal Horse 1","Pareto"),
    (8,"ME056","Manguera gasolina","Pareto"),
    (9,"6202","Aceite 4T 20W50 LST","Rotacion"),
    (10,"MZ-1450","Carter liso Owen 150","Relleno"),
    (11,"1317","Bateria GN 125","Relleno"),
    (12,"MZ-1451","Contra carter Owen 150","Relleno"),
    (13,"MZ-1770","Manguera gasolina Monster 1M","Relleno"),
    (14,"ROS37536","Aceite 4T 20W50 Rosh","Quiebre"),
    (15,"2346","Cadena dorada 428H-124L GP","Quiebre"),
 ]})

LISTAS.append({"archivo": "TERE_auditoria_profunda_07-11-2026.xlsx", "detal": "TERE", "lista": "AUDITORIA PROFUNDA",
 "quiebres": set(),
 "rows": [
    (1,"MOTUL-09","Aceite 4T 20W50 Motul 3000","Aceite"),
    (2,"ROS37539","Aceite 4T 10W50 Rosh","Aceite"),
    (3,"1136","Aceite 4T Sintetico 15W50 GP","Aceite"),
    (4,"CASTROL-04","Aceite Castrol 4T Sintetico 20W50","Aceite"),
    (5,"EG-87.8810.2.DM","Casco Phoenix Rush negro/naranja M","Casco"),
    (6,"EG-87.12.2.RG","Casco Phoenix solido gris/rojo M","Casco"),
    (7,"2528","Caucho 90/90-10 TL GP","Caucho"),
    (8,"2590","Caucho 300-10 TL Bera","Caucho"),
    (9,"R-078","Caucho 120/80-17 Duro Power","Caucho"),
    (10,"VK394","Amortiguador New Horse LJ","Amortiguador"),
    (11,"MZ-1191","Amortiguador aire Arsen 2 Rojo","Amortiguador"),
    (12,"MO-366","Bateria DR 650 YTX9 seca","Bateria"),
    (13,"MO-009","Bateria Jaguar 12N6.5 seca","Bateria"),
    (14,"MO-440","Anti espiche grande 500ml","Cruce"),
    (15,"MO-104","Banda freno GN 125","Otro"),
    (16,"MO-788","Rin del/tras 72 rayos EK Express","Rin"),
    (17,"2736","Cigueñal CG200 estria","Otro"),
    (18,"Z873","Caja cambio Owen GS Rey","Otro"),
    (19,"1038-0001","Bomba aceite AX100","Otro"),
    (20,"MO-753","Intercomunicador casco","Otro"),
 ]})

LISTAS.append({"archivo": "PALO_VERDE_07-11-2026.xlsx", "detal": "PALO_VERDE", "lista": "REGULAR",
 "quiebres": set(),
 "rows": [
    (1,"JD578","Tirrap blanco 450mm","Pareto"),
    (2,"MO-019","Caucho 275-18 TT","Pareto"),
    (3,"JD579","Tirrap blanco 500mm","Pareto"),
    (4,"CVZC082","Caucho 90/90-18 CVZ","Pareto"),
    (5,"JDM-4756","Caucho 130/80-17 Meiky","Pareto"),
    (6,"JG-1000","Amortiguador KLR 650","Pareto"),
    (7,"MO-794","Equipo prueba electrica","Pareto"),
    (8,"CVZC080","Caucho 360-18 CVZ","Pareto"),
    (9,"LJ337","Anti espiche 350ml","Rotacion"),
    (10,"Z369","Bujia CG150 NGK","Rotacion"),
    (11,"CVZR020","Rolinera 6204","Rotacion"),
    (12,"MOTUL-09","Aceite 4T 20W50 Motul","Rotacion"),
    (13,"TS970-1208016HG","Caucho 120/80-16 Timsum","Relleno"),
    (14,"Z1389","Camara Bera R1","Relleno"),
    (15,"LD137","Defensa slider rojo","Relleno"),
 ]})

LISTAS.append({"archivo": "CUA_07-11-2026.xlsx", "detal": "CUA", "lista": "REGULAR",
 "quiebres": {"11327"},
 "rows": [
    (1,"VK76","Tubo escape Horse 2","Pareto"),
    (2,"TS970-1208016HG","Caucho 120/80-16 Timsum","Pareto"),
    (3,"18408","Rin trasero Escuda","Pareto"),
    (4,"MO-788","Rin 72 rayos EK Express","Pareto"),
    (5,"JDM-7462","Caucho 275/18 Meiky","Pareto"),
    (6,"10184","Tacometro SBR digital","Pareto"),
    (7,"LJ871","Caja cambio Owen 150","Pareto"),
    (8,"EG-87.12.2.DM","Casco Phoenix gris M","Pareto"),
    (9,"MZ-6204","Rolinera 6204","Rotacion"),
    (10,"MO-440","Anti espiche 500ml","Rotacion"),
    (11,"E480","Camara completa GN125","Relleno"),
    (12,"10207","Tacometro digital Horse","Relleno"),
    (13,"EK-127","Tanque RK200 negro","Relleno"),
    (14,"MZ-1770","Manguera gasolina Monster 1M","Relleno"),
    (15,"11327","SKU justificado 05/11","Quiebre"),
 ]})

LISTAS.append({"archivo": "URBINA_07-11-2026.xlsx", "detal": "URBINA", "lista": "REGULAR",
 "quiebres": {"Z2210"},
 "rows": [
    (1,"JG-1000","Amortiguador KLR 650","Pareto"),
    (2,"CVZC082","Caucho 90/90-18 CVZ","Pareto"),
    (3,"R-074","Tirrap metalico 500mm","Pareto"),
    (4,"R-044","Tirrap negro 250mm","Pareto"),
    (5,"2595","Caucho 275-18 GP","Pareto"),
    (6,"MO-019","Caucho 275-18 TT","Pareto"),
    (7,"JDM-4756","Caucho 130/80-17 Meiky","Pareto"),
    (8,"ULTRA-02","Aceite 20W50 Ultralub","Pareto"),
    (9,"MZ-6204","Rolinera 6204","Rotacion"),
    (10,"2513","Caucho 90/90-18 GP","Rotacion"),
    (11,"JD577","Tirrap blanco 400mm","Relleno"),
    (12,"ROS37539","Aceite 4T 10W50 Rosh","Relleno"),
    (13,"RI-12","Rin delantero BSN","Relleno"),
    (14,"MZ-1770","Manguera gasolina Monster 1M","Relleno"),
    (15,"Z2210","Banda freno GN 125 marron","Quiebre"),
 ]})

LISTAS.append({"archivo": "LA_RAIZA_07-11-2026.xlsx", "detal": "LA_RAIZA", "lista": "REGULAR",
 "quiebres": set(),
 "rows": [
    (1,"ROS37536","Aceite 4T 20W50 Rosh","Pareto"),
    (2,"R-045","Tirrap negro 400mm","Pareto"),
    (3,"R-888","Caja fusible 120 pz","Pareto"),
    (4,"821","Aceite 4T 20W50 Shell","Pareto"),
    (5,"2595","Caucho 275-18 GP","Pareto"),
    (6,"MO-020","Caucho 90/90-18 Mobile","Pareto"),
    (7,"MO-017","Caucho 110/90-16 Mobile","Pareto"),
    (8,"MO-019","Caucho 275-18 TT","Pareto"),
    (9,"6202","Aceite 4T 20W50 LST","Rotacion"),
    (10,"IP-801091","Aceite 4T 20.5 IPONE","Rotacion"),
    (11,"6238","Tripa 300-18 GP","Rotacion"),
    (12,"SKY03","Rin trasero Horse 1","Relleno"),
    (13,"CVZC082","Caucho 90/90-18 CVZ","Relleno"),
    (14,"IP-801087","Aceite 4T 15W50 IPONE","Relleno"),
    (15,"MO-009","Bateria Jaguar 12N6.5","Relleno"),
 ]})

LISTAS.append({"archivo": "CHARALLAVE_07-11-2026.xlsx", "detal": "CHARALLAVE", "lista": "REGULAR",
 "quiebres": set(),
 "rows": [
    (1,"ROS37536","Aceite 4T 20W50 Rosh","Pareto"),
    (2,"ROS37363","Aceite carro 20W50 Rosh","Pareto"),
    (3,"ROS37248","Aceite 2T Rosh","Pareto"),
    (4,"1317","Bateria GN 125","Pareto"),
    (5,"ROS37539","Aceite 4T 10W50 Rosh","Pareto"),
    (6,"CVZC080","Caucho 360-18 CVZ","Pareto"),
    (7,"TS970-1208016HG","Caucho 120/80-16 Timsum","Pareto"),
    (8,"10198","Tacometro New Owen","Pareto"),
    (9,"VK76","Tubo escape Horse 2","Relleno"),
    (10,"18408","Rin trasero Escuda","Relleno"),
    (11,"R-247","Caucho 110/80-17 Duro Power","Relleno"),
    (12,"MO-788","Rin 72 rayos EK Express","Relleno"),
    (13,"JG-706","Tubo escape Outlook","Relleno"),
    (14,"4358","Kit rodamiento Horse 1","Relleno"),
    (15,"1373","Bateria Jaguar 12N6.5 litio","Relleno"),
 ]})

HEADERS = ["#", "SKU", "DESCRIPCION", "CONTEO FISICO", "HORA"]
HEADER_FILL  = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT  = Font(bold=True, color="FFFFFF")
QUIEBRE_FILL = PatternFill("solid", fgColor="FFF2CC")
BLANCO_FILL  = PatternFill("solid", fgColor="FFFFFF")
THIN   = Side(style="thin", color="B0B0B0")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

for cfg in LISTAS:
    wb = Workbook()
    ws = wb.active
    ws.title = cfg["detal"][:31]

    title = "DETAL: " + cfg["detal"] + " - FECHA: 07/11/2026 - LISTA: " + cfg["lista"]
    if cfg["quiebres"]:
        title += " - QUIEBRES: " + ", ".join(sorted(cfg["quiebres"]))

    ws.merge_cells("A1:E1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=13)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    for col, h in enumerate(HEADERS, start=1):
        c = ws.cell(row=2, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDER
        c.protection = Protection(locked=True)
    ws.row_dimensions[2].height = 22

    for i, (num, sku, desc, tipo) in enumerate(cfg["rows"], start=3):
        es_quiebre = (sku in cfg["quiebres"]) or (str(tipo).lower() == "quiebre")

        for col, val in [(1, num), (2, sku), (3, desc)]:
            c = ws.cell(row=i, column=col, value=val)
            c.border = BORDER
            c.protection = Protection(locked=True)
            c.alignment = Alignment(vertical="center",
                                    horizontal="center" if col == 1 else "left",
                                    wrap_text=(col == 3))
            if es_quiebre:
                c.fill = QUIEBRE_FILL

        d = ws.cell(row=i, column=4, value=None)
        d.border = BORDER
        d.fill = BLANCO_FILL
        d.protection = Protection(locked=False)
        d.number_format = "0"
        d.alignment = Alignment(horizontal="center", vertical="center")

        e = ws.cell(row=i, column=5, value=None)
        e.border = BORDER
        e.fill = BLANCO_FILL
        e.protection = Protection(locked=False)
        e.number_format = "hh:mm"
        e.alignment = Alignment(horizontal="center", vertical="center")

    for col, w in {"A":5,"B":20,"C":48,"D":16,"E":12}.items():
        ws.column_dimensions[col].width = w

    ws.freeze_panes = "A3"
    ws.protection.sheet = True
    ws.protection.password = PASSWORD
    ws.protection.formatCells   = False
    ws.protection.formatColumns = True
    ws.protection.formatRows    = True
    ws.protection.insertRows    = True
    ws.protection.deleteRows    = True

    path = os.path.join(OUTDIR, cfg["archivo"])
    wb.save(path)
    print("Generado:", path)

print("Listo: 7 Excel generados en la carpeta", OUTDIR)
