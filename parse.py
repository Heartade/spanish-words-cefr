from bs4 import BeautifulSoup
import re
import requests
all_words = set('')
all_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
words_by_level = {}
for level in all_levels:
    words_by_level[level] = set()


def parse(url: str, page_number: int = 0, levels: list = ['A1', 'A2']):
    """
    Parse the curriculum pages of the Cervantes Institute.
    The curriculum pages are organized by topic (h1), section (h2), subsection (h3), and contents.

    The h3 tags are hidden, with the actual subsection name displayed in table <caption>,
    but they are used to organize the contents of the h2 sections.

    The contents are presented as a table with two rows and two columns,
    where the header row (th) signifies each level;
    and the content row (tr) signifies the contents for the level.

    The contents are words in Spanish, which are parsed and written to a csv file for each level.
    The filename follows the form of "A1_8_Nociones_generales.csv".

    url: The url of the curriculum page.
    page_number: The page number of the curriculum page.
    levels: The levels to parse from the curriculum page.
    
    returns: A list of words in the page for each level.
    """
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    h1 = soup.find('h1')
    # Page title follows the form of "Nociones generales. Inventario A1-A2"
    title = h1.text.strip().split('.')[0]
    title_underbar = title.replace(' ', '_')
    # Create a csv file for each level.
    outputs = [open(f'{level}_{page_number}_{title_underbar}.csv',
                    'w', encoding='utf-8') for level in levels]
    for output in outputs:
        output.write('"Section","Subsection","Word"\n')
    h2 = soup.find('h2')
    counts = [0, 0]
    words_in_page_by_level = [set(), set()]
    while h2 is not None:
        section = h2.text.strip()
        h3 = h2.find_next('h3')
        h2 = h2.find_next_sibling('h2')
        # h3 sections between h2 sections
        while h3 is not None and (h2 is None or h3.sourceline < h2.sourceline):
            subsection = h3.text.strip()
            row = h3.find_next('tr')
            h3 = h3.find_next_sibling('h3')
            # table rows between h3 sections
            while row is not None and (h3 is None or row.sourceline < h3.sourceline):
                cell = row
                # for each cell representing a level in the subsection
                for i in range(2):
                    cell = cell.find_next('td')
                    # remove all non-spanish characters
                    cell_text = re.sub(
                        r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ ]', ' ', cell.text)
                    # remove extra spaces
                    cell_text = re.sub(r' +', ' ', cell_text).strip()
                    if cell_text == '':
                        continue
                    # list of words that appear in a cell
                    # which presents contents of a subsection for a level
                    list_words = cell_text.split(' ')
                    # remove words that have appeared before
                    set_words = set()
                    for word in list_words:
                        if word == word.lower() and word not in all_words:
                            set_words.add(word)
                            all_words.add(word)
                    # write to csv
                    for word in set_words:
                        outputs[i].write(
                            f'"{section}","{subsection}","word"\n')
                    counts[i] += len(set_words)
                    words_in_page_by_level[i].update(set_words)
                row = row.find_next_sibling('tr')
    print(f"Section {page_number}: {title}")
    print(f"Level {levels[0]}: {counts[0]: >4d} words")
    print(f"Level {levels[1]}: {counts[1]: >4d} words")
    return words_in_page_by_level


# download the files and parse
docs = [
    [8, ['A1', 'A2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/08_nociones_generales_inventario_a1-a2.htm'],
    [8, ['B1', 'B2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/08_nociones_generales_inventario_b1-b2.htm'],
    [8, ['C1', 'C2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/08_nociones_generales_inventario_c1-c2.htm'],
    [9, ['A1', 'A2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/09_nociones_especificas_inventario_a1-a2.htm'],
    [9, ['B1', 'B2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/09_nociones_especificas_inventario_b1-b2.htm'],
    [9, ['C1', 'C2'], 'https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/niveles/09_nociones_especificas_inventario_c1-c2.htm']
]

for doc in docs:
    section_number = doc[0]
    levels_in_page = doc[1]
    url = doc[2]
    result = parse(url, section_number, levels_in_page)
    for i in range(2):
        words_by_level[levels_in_page[i]].update(result[i])

print(f"Total: {len(all_words)} words")

for level in all_levels:
    output = open(level + '_all_raw.csv', 'w', encoding='utf-8')
    output.write('\n'.join(words_by_level[level]))
    output.close()
