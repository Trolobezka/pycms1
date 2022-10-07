import sys
import math
import re
from enum import Enum
from subprocess import Popen
from os import makedirs
from os.path import isdir, isfile
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QStyle,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QPalette, QColor
from PyQt6.QtCore import Qt

G = TypeVar("G")


def rewrite_file_with_new_values(
    output_filename: str, variables: Dict[str, str]
) -> Tuple[bool, str]:

    name_regex_raw: str = "(?<=\\\\newcommand\\{\\\\).+?(?=\\})"
    value_regex_raw: str = "(?<=}{).+?(?=\\})"

    name_regex: re.Pattern[str] = re.compile(name_regex_raw)
    value_regex: re.Pattern[str] = re.compile(value_regex_raw)

    var_start_seen: bool = False
    var_end_seen: bool = False

    if not isdir("./out"):
        makedirs("./out")

    try:
        input_file = open("./tex/u1_template.tex", "r", encoding="utf-8")
        output_file = open(f"./out/{output_filename}.tex", "wb")
    except Exception as e:
        return (False, "Exception while opening the files:\n" + str(e))

    for line in input_file:
        new_line: str = line

        if not var_start_seen and "% variables start" in line:
            var_start_seen = True
        elif not var_end_seen and "% variables end" in line:
            var_end_seen = True

        if var_start_seen and not var_end_seen:
            name_match: Optional[re.Match[str]] = next(name_regex.finditer(line), None)
            if name_match is not None:
                print(name_match.group(0))
            if name_match is not None and name_match.group(0) in variables:
                value: str = variables[name_match.group(0)]
                new_line, n = value_regex.subn(value, line)
                if n != 1:
                    print(
                        f"WARNING: subn returned {n}, current line is '{line}', new line is '{new_line}'."
                    )

        output_file.write(new_line.encode("utf-8"))
    input_file.close()
    output_file.close()

    return (True, "")


# https://stackoverflow.com/a/71609384/9318084
def num_zeros(value: float) -> int:
    return -math.floor(math.log10(abs(value))) - 1


# https://stackoverflow.com/a/2440786/9318084
def float_to_latex(value: float) -> str:
    if value == 0:
        return "0"
    zeros: int = num_zeros(value)
    if zeros > 3:
        splits: List[str] = format(value, ".3e").split("e-")
        splits[0] = splits[0].rstrip("0").rstrip(".")
        splits[1] = splits[1].lstrip("0")
        return "\\ensuremath{" + splits[0] + "\\cdot{10^{-" + splits[1] + "}}}"
    elif zeros < 0:
        if value > 1000:
            return str(round(value))
        return format(round(value, 3), ".3f").rstrip("0").rstrip(".")
    return format(round(value, zeros + 3), ".6f").rstrip("0").rstrip(".")


def try_parse_int(value: Any, _default: int = 0) -> int:
    try:
        return int(value)
    except:
        return _default


def try_parse_float(value: Any, _default: float = 0) -> float:
    try:
        return float(value)
    except:
        return _default


def format_variable(
    symbol: str, sub: str = "", sup: str = "", use_table: bool = False
) -> str:
    if use_table:
        return (
            (
                "<table>"
                "<tr>"
                '<td rowspan="2" valign="middle">$1</td>'
                '<td align="left"><sub>$2</sub></td>'
                "</tr>"
                "<tr>"
                '<td align="left"><sup>$3</sup></td>'
                "</tr>"
                "</table>"
            )
            .replace("$1", symbol)
            .replace("$2", sup)
            .replace("$3", sub)
        )
    else:
        return f"{symbol}<sub>{sub}</sub><sup>{sup}</sup>"


class GreekLetters(str, Enum):
    sigma = "\u03C3"
    tau = "\u03C4"


class InputLine(QWidget):
    def __init__(
        self,
        description: str,
        symbol: str,
        unit: str,
        parent: Optional[QWidget] = None,
        flags: Qt.WindowType = Qt.WindowType.Widget,
    ) -> None:
        super().__init__(parent, flags)

        self.parts: List[QWidget] = [
            QLabel(description),
            QLabel(symbol),
            QLineEdit(),
            QLabel(unit),
        ]

        hbox = QHBoxLayout()
        for part in self.parts:
            hbox.addWidget(part)
        self.setLayout(hbox)


class IOVariable(object):
    def __init__(
        self,
        description: str,
        symbol: Union[str, Tuple[str, str, str]],
        default_value: Union[int, float, str],
        unit: str,
        is_input: bool,
        is_header: bool = False,
    ) -> None:
        self.description: str = description
        if isinstance(symbol, Tuple):
            symbol = format_variable(symbol[0], symbol[1], symbol[2])
        self.symbol: str = symbol
        self.default_value: Union[int, float, str] = default_value
        self.value: Union[int, float, str] = default_value
        self.unit: str = unit
        self.is_input: bool = is_input
        self.is_header: bool = is_header


class VariableStore(object):
    def __init__(self) -> None:
        def make_header(s: str) -> IOVariable:
            return IOVariable(s, "", 0, "", False, is_header=True)

        self.input_header = make_header("Vstupní hodnoty")
        self.jmeno = IOVariable("Jméno autora", "", "Autor", "", True)
        self.motorN = IOVariable("Otáčky motoru", "n", 1500, "ot/min", True)
        self.dmin = IOVariable(
            "Minimální průměr hřídele", ("d", "min", ""), 24, "", True
        )
        self.AxZa = IOVariable("Axiální zajištění", "", "Nord-Lock", "", True)
        self.MatNa = IOVariable("Materiál náboje (řetězky)", "", "C43", "", True)
        self.MatHr = IOVariable("Materiál hřídele", "", "S275 JR", "", True)
        self.tauDovHridel = IOVariable(
            "Dovolené napětí hřídele ve střihu",
            (GreekLetters.tau, "dov", ""),
            20,
            "MPa",
            True,
        )

        self.shaftbore_header = make_header("Spoj hřídele a náboje")
        self.pDMin = IOVariable(
            "Min. dovolený tlak ve spoji", ("p", "dovmin", ""), 80, "MPa", True
        )
        self.pDMax = IOVariable(
            "Max. dovolený tlak ve spoji", ("p", "dovmax", ""), 120, "MPa", True
        )
        self.pD = IOVariable(
            "Dovolený tlak ve spoji", ("p", "dov", ""), 80, "MPa", True
        )

        self.key_header = make_header("Pero")
        self.dhr = IOVariable("Průměr hřídele pod perem", "d", 30, "mm", True)
        self.bPera = IOVariable("Šířka pera", "b", 8, "mm", True)
        self.hPera = IOVariable("Výška pera", "h", 7, "mm", True)
        self.lPera = IOVariable("Délka pera", "l", 25, "mm", True)
        self.tauDMin = IOVariable(
            "Min. dovolené napětí pera ve střihu",
            (GreekLetters.tau, "dovmin", ""),
            60,
            "MPa",
            True,
        )
        self.tauDMax = IOVariable(
            "Max. dovolené napětí pera ve střihu",
            (GreekLetters.tau, "dovmax", ""),
            90,
            "MPa",
            True,
        )
        self.tauD = IOVariable(
            "Dovolené napětí pera ve střihu",
            (GreekLetters.tau, "dov", ""),
            60,
            "MPa",
            True,
        )

        self.spline_header = make_header("Drážkování")
        self.nDraz = IOVariable("Počet zubů drážkování", "n", 6, "", True)
        self.dDraz = IOVariable("Malý průměr drážkování", "d", 26, "mm", True)
        self.DDraz = IOVariable("Velký průměr drážkování", "D", 32, "mm", True)
        self.bDraz = IOVariable("Šířka zubu drážkování", "b", 6, "mm", True)
        self.Adr = IOVariable("Účinná plocha drážkování na 1 mm", "A'", 9.9, "mm", True)
        self.lKoefMinDraz = IOVariable(
            "Koef. doporučené min. délky drážkování (od)",
            ("k", "lmin1", ""),
            1.4,
            "",
            True,
        )
        self.lKoefMaxDraz = IOVariable(
            "Koef. doporučené min. délky drážkování (do)",
            ("k", "lmin2", ""),
            1.5,
            "",
            True,
        )
        self.lDraz = IOVariable("Zvolená délka drážkování", "l", 38, "mm", True)

        # Outputs
        self.result_header = make_header("Výsledky")
        self.Mk = IOVariable("Kroutící moment", ("M", "k2", ""), 54285, "Nmm", False)
        self.laPera = IOVariable("Aktivní délka pera", ("l", "a", ""), 17, "mm", False)
        self.pSkut = IOVariable("Tlak působící na pero", "p", 60.82, "MPa", False)
        self.otlacVysledek = IOVariable(
            "Výsledek kontroly otlačení pera", "", "VYHOVUJE", "", False
        )
        self.tauSkut = IOVariable(
            "Napětí pera ve střihu", GreekLetters.tau, 26.61, "MPa", False
        )
        self.strihVysledek = IOVariable(
            "Výsledek kontroly střihu pera", "", "VYHOVUJE", "", False
        )
        self.lMinDraz = IOVariable(
            "Doporučená min. délka drážkování (od)",
            ("l", "min1", ""),
            36.4,
            "mm",
            False,
        )
        self.lMaxDraz = IOVariable(
            "Doporučená min. délka drážkování (do)", ("l", "min2", ""), 39, "mm", False
        )
        self.pSkutDraz = IOVariable(
            "Skutečný tlak v drážkování", "p", 9.95, "MPa", False
        )
        self.drazVysledek = IOVariable(
            "Výsledek kontroly otlačení drážkování", "", "VYHOVUJE", "", False
        )

        self.variables: Dict[str, IOVariable] = {}
        for name, value in self.__dict__.items():
            if isinstance(value, IOVariable):
                self.variables[name] = value


class GridInput(QWidget):
    def __init__(
        self,
        variables: List[IOVariable],
        parent: Optional[QWidget] = None,
        flags: Qt.WindowType = Qt.WindowType.Widget,
    ) -> None:
        super().__init__(parent, flags)

        self.variables: Dict[IOVariable, List[QWidget]] = {}

        self.grid = QGridLayout()
        for y, variable in enumerate(variables):
            if variable.is_header:
                self.variables[variable] = [QLabel(f"<h2>{variable.description}</h2>")]
            else:
                self.variables[variable] = [
                    QLabel(variable.description),
                    QLabel(variable.symbol),
                    QLineEdit(str(variable.value)),
                    QLabel(variable.unit),
                ]
            if not variable.is_input and not variable.is_header:
                cast(QLineEdit, self.variables[variable][2]).setReadOnly(
                    not variable.is_input
                )
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Base, QColor("lightgray"))
                cast(QLineEdit, self.variables[variable][2]).setPalette(palette)
            for x, widget in enumerate(self.variables[variable]):
                self.grid.addWidget(widget, y, x)
        self.setLayout(self.grid)

    def sync_data(self) -> None:
        for iovar, widgets in self.variables.items():
            if (
                not iovar.is_header
                and iovar.is_input
                and isinstance(widgets[2], QLineEdit)
            ):
                value: Union[int, float, str] = ""
                text: str = widgets[2].text()
                if isinstance(iovar.default_value, int):
                    value = try_parse_int(text)
                elif isinstance(iovar.default_value, float):
                    value = try_parse_float(text)
                elif isinstance(iovar.default_value, str):
                    value = text
                else:
                    raise TypeError()
                iovar.value = value

    def get_value(self, variable: IOVariable, _type: Type[G]) -> G:
        line_edit = self.variables[variable][2]
        if isinstance(line_edit, QLineEdit):
            text = line_edit.text()
            if _type is int:
                return cast(G, try_parse_int(text))
            elif _type is float:
                return cast(G, try_parse_float(text))
            elif _type is str:
                return cast(G, str(text))
        raise ValueError()

    def set_value(self, variable: IOVariable, value: Union[int, float, str]) -> None:
        line_edit = self.variables[variable][2]
        if isinstance(line_edit, QLineEdit):
            variable.value = value
            line_edit.setText(str(value))


class Window(QWidget):
    def fix_scroll_area_size(self) -> None:
        self.scroll_area.setMinimumWidth(self.grid_for_variables.sizeHint().width())

    def font_plus(self) -> None:
        f = self.font()
        f.setPointSize(f.pointSize() + 1)
        self.setFont(f)
        self.fix_scroll_area_size()

    def font_minus(self) -> None:
        f = self.font()
        f.setPointSize(f.pointSize() - 1)
        self.setFont(f)
        self.fix_scroll_area_size()

    def print_variables(self) -> None:
        print("========= INPUT ===========")
        for name, iovar in self.variable_store.variables.items():
            if iovar.is_input and not iovar.is_header:
                val = self.grid_for_variables.get_value(iovar, str)
                print(f"{name} = {val} {iovar.unit}")
        print("========= OUTPUT ==========")
        for name, iovar in self.variable_store.variables.items():
            if not iovar.is_input and not iovar.is_header:
                val = self.grid_for_variables.get_value(iovar, str)
                print(f"{name} = {val} {iovar.unit}")
        print("===========================")

    def calculate(self) -> None:
        self.grid_for_variables.sync_data()
        self.print_variables()

        vs: VariableStore = self.variable_store

        def gv(v: IOVariable, t: Type[G]) -> G:
            return self.grid_for_variables.get_value(v, t)

        tauDovHridel: float = gv(vs.tauDovHridel, float)
        dmin: float = gv(vs.dmin, float)

        Mk: float = (math.pi * tauDovHridel * dmin**3) / 16
        self.grid_for_variables.set_value(vs.Mk, Mk)

        lPera: float = gv(vs.lPera, float)
        bPera: float = gv(vs.bPera, float)

        laPera: float = lPera - bPera
        self.grid_for_variables.set_value(vs.laPera, laPera)

        dhr: float = gv(vs.dhr, float)
        hPera: float = gv(vs.hPera, float)

        pSkut: float = (4 * Mk) / (dhr * hPera * laPera)
        self.grid_for_variables.set_value(vs.pSkut, pSkut)

        pD: float = gv(vs.pD, float)
        if pSkut <= pD:
            self.grid_for_variables.set_value(vs.otlacVysledek, "VYHOVUJE")
        else:
            self.grid_for_variables.set_value(vs.otlacVysledek, "NEVYHOVUJE")

        tauSkut: float = (2 * Mk) / (dhr * bPera * laPera)
        self.grid_for_variables.set_value(vs.tauSkut, tauSkut)

        tauD: float = gv(vs.tauD, float)
        if tauSkut <= tauD:
            self.grid_for_variables.set_value(vs.strihVysledek, "VYHOVUJE")
        else:
            self.grid_for_variables.set_value(vs.strihVysledek, "NEVYHOVUJE")

        dDraz: float = gv(vs.dDraz, float)
        lKoefMinDraz: float = gv(vs.lKoefMinDraz, float)
        lKoefMaxDraz: float = gv(vs.lKoefMaxDraz, float)

        lMinDraz: float = lKoefMinDraz * dDraz
        lMaxDraz: float = lKoefMaxDraz * dDraz
        self.grid_for_variables.set_value(vs.lMinDraz, lMinDraz)
        self.grid_for_variables.set_value(vs.lMaxDraz, lMaxDraz)

        ADraz: float = gv(vs.Adr, float)
        lDraz: float = gv(vs.lDraz, float)
        DDraz: float = gv(vs.DDraz, float)

        pSkutDraz: float = (4 * Mk) / (ADraz * lDraz * (DDraz + dDraz))
        self.grid_for_variables.set_value(vs.pSkutDraz, pSkutDraz)

        if pSkutDraz <= pD:
            self.grid_for_variables.set_value(vs.drazVysledek, "VYHOVUJE")
        else:
            self.grid_for_variables.set_value(vs.drazVysledek, "NEVYHOVUJE")

        msg = QMessageBox()
        msg.setWindowTitle("Informace")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"Výpočet proběhl úspěšně.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def create_tex_file(self) -> None:
        self.grid_for_variables.sync_data()
        self.print_variables()

        def var_to_str(var: Union[int, float, str]) -> str:
            if isinstance(var, int) or isinstance(var, float):
                print(var)
                s = float_to_latex(var)
                return s
            else:
                return str(var)

        tex_variables: Dict[str, str] = {
            name: var_to_str(iovar.value)
            for name, iovar in self.variable_store.variables.items()
        }
        result = rewrite_file_with_new_values("u1", tex_variables)

        msg = QMessageBox()
        if result[0]:
            msg.setWindowTitle("Informace")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Soubor .tex vytvořen ve složce ./out.")
        else:
            msg.setWindowTitle("Upozornění")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(
                "Při tvorbě .tex souboru nastala chyba. Chybové hlášení:\n" + result[1]
            )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        retval = msg.exec()
        print(f"MessageBox return value: {retval}")

    def run_pdflatex(self) -> None:
        if isdir("./out") and isfile("./out/u1.tex"):
            print("Running pdflatex:")
            popen1 = Popen("pdflatex -output-directory=out .\\out\\u1.tex", shell=True)
            popen1.wait()
            popen2 = Popen("pdflatex -output-directory=out .\\out\\u1.tex", shell=True)
            popen2.wait()
            retval1 = popen1.returncode
            retval2 = popen2.returncode
            print(retval1, retval2)
            print("Opening pdf:")
            popen3 = Popen("start ./out/u1.pdf", shell=True)
            popen3.wait()
            retval3 = popen3.returncode
            print(retval3)

            msg_text: str = ""
            if retval1 == 0 and retval2 == 0 and retval3 == 0:
                msg_text = "Soubor .pdf vytvořen ve složce ./out."
            else:
                msg_text = (
                    "Myslím si, že někde došlo k chybě. "
                    "Pokud soubor .pdf není vytvořen ve složce ./out, zkontrolujte, "
                    "že máte nainstalovaný pdfLaTeX (a cestu k němu přidanou do proměnné prostředí PATH). "
                    "Můžete také zkusit zkompilovat soubor .tex pomocí Vámi zvoleného TeX 'endžinu' (LaTeX, XeLaTeX, LuaLaTeX/LuaTeX)."
                )

            msg = QMessageBox()
            msg.setWindowTitle("Informace")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(msg_text)
            msg.setDetailedText(
                f"retval1 = {retval1}\nretval2 = {retval2}\nretval3 = {retval3}"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Informace")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Soubor .tex neexistuje.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ČMS1 Úloha 1")

        self.scroll_area = QScrollArea()
        self.vbox = QVBoxLayout()

        # FONT BUTTONS

        self.font_button_container = QWidget()
        self.font_button_container.setLayout(QHBoxLayout())

        btn = QPushButton("Zoom +")
        btn.clicked.connect(self.font_plus)
        self.font_button_container.layout().addWidget(btn)
        btn = QPushButton("Zoom -")
        btn.clicked.connect(self.font_minus)
        self.font_button_container.layout().addWidget(btn)

        self.vbox.addWidget(self.font_button_container)

        # VARIABLE GRID

        self.variable_store = VariableStore()
        self.grid_for_variables = GridInput(
            list(self.variable_store.variables.values())
        )
        for iovar in self.variable_store.variables.values():
            if not iovar.is_input and not iovar.is_header:
                self.grid_for_variables.set_value(iovar, "")

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.grid_for_variables)
        self.vbox.sizeHint()

        self.fix_scroll_area_size()
        self.vbox.addWidget(self.scroll_area)

        # CALCULATE, PRINT, PDF BUTTON

        self.calculate_button_container = QWidget()
        self.calculate_button_container.setLayout(QHBoxLayout())

        btn = QPushButton("(1) Vypočítej")
        btn.clicked.connect(self.calculate)
        self.calculate_button_container.layout().addWidget(btn)

        btn = QPushButton("(2) Vytvoř .tex soubor")
        btn.clicked.connect(self.create_tex_file)
        self.calculate_button_container.layout().addWidget(btn)

        btn = QPushButton("(3) pdfLaTeX")
        btn.clicked.connect(self.run_pdflatex)
        self.calculate_button_container.layout().addWidget(btn)

        self.vbox.addWidget(self.calculate_button_container)

        # MAIN LAYOUT

        self.vbox.addWidget(QLabel("Vytvořil Richard Kokštein, 2022."))
        self.setLayout(self.vbox)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
