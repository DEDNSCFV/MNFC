# Contribuir a MNFC

Gracias por tu interes en MNFC. Antes de enviar un pull request, lee
esta guia completa.

---

## CLA obligatorio

MNFC se distribuye bajo **licencia dual** (AGPL-3.0 OR Commercial).
Para preservar esa dualidad, toda contribucion requiere aceptacion
previa del Contributor License Agreement (CLA).

Sin CLA, el contribuyente retiene el copyright de su parte, y el autor
original **no puede relicenciar comercialmente** codigo que no es
enteramente suyo. Eso rompe la licencia dual.

### Aceptacion del CLA

Al enviar un pull request a MNFC, declaras y aceptas:

1. **Cesion de derechos**: cedes al autor original
   (Domingo Eduardo Diaz Navas) el derecho irrevocable, mundial y
   libre de regalias de relicenciar tu contribucion bajo cualquier
   licencia, incluida la licencia comercial de MNFC.

2. **Originalidad**: garantizas que tu contribucion es obra original
   tuya, o que tienes permiso suficiente para cederla bajo estos
   terminos.

3. **Sin conflicto de derechos**: garantizas que tu contribucion no
   viola derechos de terceros (copyright, patentes, marcas).

4. **Sujecion a la licencia dual**: aceptas que tu contribucion queda
   sujeta a la licencia dual de MNFC (AGPL-3.0-or-later OR Commercial).

Si no aceptas estos terminos, no envies un pull request. Puedes abrir
un issue proponiendo la mejora sin aportar codigo.

---

## Flujo de trabajo

1. **Fork** del repositorio.
2. **Rama** con nombre descriptivo:
   - `fix/xyz` para correcciones
   - `feat/xyz` para nuevas funciones
   - `docs/xyz` para documentacion
   - `test/xyz` para tests
3. **Tests pasando** antes de abrir el PR:
   ```bash
   pytest tests/
4. Firma los commits (SSH o GPG). El repositorio exige commits firmados.
5. Pull request con descripcion clara:
   · Que problema resuelve
   · Como lo resuelve
   · Tests que agrega o modifica

---

Firma de commits

Todos los commits deben estar firmados con SSH o GPG. Ver
ProGit 2014 L2127 (firma y verificacion con GPG).

Configuracion minima (SSH):

```bash
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519
git config commit.gpgsign true
```

---

Estado epistemico

MNFC sigue una taxonomia de cuatro niveles para cada funcion:

· N1 - identificada (locus en raw bibliografico)
· N2 - reconstruida (notacion traducida)
· N3 - verificada (confrontada contra PDF original)
· N4 - aplicada (dominio real)

Si contribuyes a las capas 2 (estadistica), 3 (fractal) o 6 (ledger),
declara el estado epistemico de tu aporte en el PR:

· Si agregas una nueva formula: cita el locus (linea del raw).
· Si verificas contra PDF: documenta la verificacion.
· Si aplicas en dominio real: describe el caso.

Esto es parte del rigor del programa. No es burocracia: es lo que
permite decir "N3 verificado" con honestidad.

---

Estilo de codigo

· Python 3.10+.
· Sin dependencias externas (solo stdlib). Este es un principio
  de diseno del kernel.
· Docstrings con cita a locus cuando aplique.
· Sin acentos en identificadores ni en docstrings tecnicos (para
  portabilidad de encoding).
· Tests por cada funcion nueva.

---

Que se acepta

· Correcciones de bugs con test que lo demuestre.
· Nuevas formulas con locus verificado.
· Verificaciones N3 (confrontar raw contra PDF).
· Mejoras de documentacion.
· Nuevos tests que aumenten cobertura.

Que NO se acepta

· Cambios que agreguen dependencias externas.
· Cambios que rompan la API publica sin discusion previa.
· Codigo sin tests.
· Contribuciones sin CLA.
· Funciones sin locus declarado en las capas 1, 2, 3, 6.

---

Contacto

lic.dedn@gmail.com

Asunto sugerido: [MNFC] <descripcion breve>
