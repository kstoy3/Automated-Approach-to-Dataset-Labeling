import xml.etree.ElementTree as ET
import re
import glob
import json

'''
1. Split citations. end in '.\n' and lookahead for Last, F.

NER model to pick up people/organizations? Probably overkill

    Look for http://disc.sci.gsfc.nasa Or Goddard Earth Sciences in addition to explicit mentions
    
    Is it faster to just add the references section if it contains any and then split later
    
    TODO!! DOI LOWERCASE!!
'''


def search_occurrences(keyword):
    occurrences = re.findall(r'.{,130}\n?.{,130}' + keyword + '.{,70}\n?.{,70}', text)
    if occurrences:
        print(occurrences, file_name)


if __name__ == '__main__':
    # User parameters
    search_text_too = True  # search the sections of the papers that are not explicity classified as 'references' for DOIs/shortnames
    free_text = True  # search for 'GES DISC' or a link to the ges disc website
    output_file_name = "free_text/forward_ges_references_and_text.json"
    cermzones_directory = '../convert_using_cermzones/forward_gesdisc/successful_cermfiles/'  # directory of CERMFILES
    doi_to_dataset_mapping_location = '../data/json/doi_to_dataset_name.json'
    dataset_long_to_short_mapping = '../data/json/dataset_long_to_short.json'

    reference_label = "GEN_REFERENCES"
    free_text_keyword = r'(?:disc\.gsfc\.nasa\.gov)|(?:GES[ -]?DISC)'
    papers_with_explicit_mentions = 0
    results = {}

    with open(doi_to_dataset_mapping_location) as f:
        doi_to_dataset = json.load(f)

    dataset_to_doi = {v: k for k, v in doi_to_dataset.items()}

    with open(dataset_long_to_short_mapping) as f:
        dataset_long_to_short = json.load(f)

    for file in glob.glob(cermzones_directory + "*.cermzones"):
        dois_founds, datasets_found, datasets_found_map = set(), set(), set()
        free_text_ges_disc_citations = []

        print(file)
        file_name = file.split("\\")[-1].replace(".cermzones", "")  # just get the pdf key of the file

        # cermzone files are stored as an XML-like document so load the text in the file into an XML tree
        tree = ET.parse(file)
        root = tree.getroot()

        for child in root.findall('./zone'):  # look at all the <zone> tags
            if child.attrib['label'] == reference_label or search_text_too:
                text = child.text

                # Remove words that might mess up splitting
                text = re.sub(r' \[CrossRef\] ?', '', text)

                if not free_text:  # we do NOT want to look for free text references
                    # search for DOI
                    for doi in doi_to_dataset:
                        matches = re.findall(rf'{doi.lower()}', text.lower())
                        # print(matches)
                        if len(matches) >= 1:
                            dois_founds.add(doi)
                            dataset_found = doi_to_dataset[doi]
                            datasets_found_map.add(dataset_found)
                            found = True

                    # search for an explicit short name or long name. Might be double counting (ie: if OMTO3d is explicitly mentioned,
                    # I may also be picking up OMTO3)
                    for long_name, short_name in dataset_long_to_short.items():
                        long_matches = re.findall(rf'{long_name}', text)
                        short_matches = re.findall(rf'{short_name}', text)
                        if len(long_matches) >= 1:
                            dataset_found = [dataset_long_to_short[lm] for lm in long_matches]
                            # datasets_found += dataset_found
                            [datasets_found.add(ds) for ds in dataset_found]
                            [datasets_found_map.add(ds) for ds in dataset_found]
                            found = True
                        elif len(short_matches) >= 1:
                            found = True
                            [datasets_found.add(ds) for ds in short_matches]
                            [datasets_found_map.add(ds) for ds in short_matches]
                else:
                    # very coarse attempt to split between references
                    splits = re.split(r'\.\n(?=(\d{1,2}\.? )?\w+, \w)', text)
                    for s in splits:
                        if not s:
                            continue
                        # print(s, '\n')
                        found = False
                        # search for dois
                        for doi in doi_to_dataset:
                            matches = re.findall(rf'{doi.lower()}', s.lower())
                            # print(matches)
                            if len(matches) >= 1:
                                dois_founds.add(doi)
                                dataset_found = doi_to_dataset[doi]
                                datasets_found_map.add(dataset_found)
                                found = True

                        # search for short names or long names (long names would get mapped to short names)
                        for long_name, short_name in dataset_long_to_short.items():
                            long_matches = re.findall(rf'{long_name}', s)
                            short_matches = re.findall(rf'{short_name}', s)
                            if len(long_matches) >= 1:
                                dataset_found = [dataset_long_to_short[lm] for lm in long_matches]
                                # datasets_found += dataset_found
                                [datasets_found_map.add(ds) for ds in dataset_found]
                                found = True
                            elif len(short_matches) >= 1:
                                # datasets_found += short_matches
                                found = True
                                [datasets_found_map.add(ds) for ds in short_matches]

                        # if did not find a DOI or a short name and this section is a reference section, look for free text matches
                        if not found and child.attrib['label'] == reference_label:
                            keyword_occurrences = re.findall(rf'{free_text_keyword}', s)
                            if len(keyword_occurrences) >= 1:
                                print(file_name, s, '-----\n')
                                free_text_ges_disc_citations.append(s)

        # if we found a doi, a short name, or a free text reference, save the result
        if len(dois_founds) >= 1 or len(datasets_found_map) >= 1 or len(free_text_ges_disc_citations):
            print(file_name, dois_founds, datasets_found_map)
            papers_with_explicit_mentions += 1
            modified_file_name = file_name.split('.')[0]
            results[modified_file_name] = {
                "explicit_dois": list(dois_founds),
                "explicit_datasets": list(datasets_found),
                "datasets_and_doi": list(datasets_found_map),
                "free_text": free_text_ges_disc_citations
            }

    print("papers with explicit dataset citations", papers_with_explicit_mentions)
    # output the result to a file
    with open(output_file_name, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)




