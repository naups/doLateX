\documentclass[{{ body_font_size }},{{ page_size }}]{report}

% --- Page layout ---
\usepackage[top={{ margin_top }}, bottom={{ margin_bottom }},
            left={{ margin_left }}, right={{ margin_right }}]{geometry}

% --- Font (Calibri via fontspec — requires XeLaTeX/LuaLaTeX) ---
\usepackage{fontspec}
\setmainfont{ {{ font_family }} }

% --- Line spacing ---
\usepackage{setspace}
\setstretch{ {{ line_spacing }} }

% --- Paragraph ---
\usepackage{indentfirst}
\setlength{\parindent}{{ first_line_indent }}
\setlength{\parskip}{{ paragraph_spacing }}
\usepackage{ragged2e}
\justifying

% --- Core packages ---
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{chngcntr}

% --- Page numbering ---
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\pagenumbering{arabic}

% --- Headings (FILKOM UB: 16pt bab, 14pt sub-bab, 12pt level 4) ---
\titleformat{\chapter}{\fontsize{{ heading_1_size }}{{ heading_1_size }}\selectfont\bfseries\centering}
             {BAB \thechapter}{0pt}{\centering}
\titlespacing{\chapter}{0pt}{0pt}{12pt}
\titleformat{\section}{\fontsize{{ heading_2_size }}{{ heading_2_size }}\selectfont\bfseries}
             {\thesection}{0pt}{}
\titleformat{\subsection}{\fontsize{{ heading_3_size }}{{ heading_3_size }}\selectfont\bfseries}
             {\thesubsection}{0pt}{}
\titleformat{\subsubsection}{\fontsize{{ heading_4_size }}{{ heading_4_size }}\selectfont\bfseries}
             {\thesubsubsection}{0pt}{}

% --- Source code (Courier New 9pt, numbered) ---
\lstset{
    basicstyle=\fontsize{9pt}{11pt}\ttfamily,
    numbers=left,
    numberstyle=\tiny,
    stepnumber=1,
    numbersep=5pt,
    frame=single,
    breaklines=true,
    columns=fixed,
}
