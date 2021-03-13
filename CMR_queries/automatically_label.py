import json
import re
from collections import defaultdict
from CMR_Queries.manually_reviewed_utilities import *
from CMR_Queries.sentence_label_utilities import *
from datetime import datetime

'''
key: {
    key
    article_name
    file_name
    manually_reviewed_datasets
    sentences with instrument, platform, model
        MORE STUFF HERE
    summary stats
    *******************************
    Per citation generate a json file containing:
    Article name, key, file name
    Manually identified datasets, if available
    
    The sentences that contain at least one of the GES DISC instruments, platforms or models
    Summary statistics:
        Instrument/platform pair counts
        Single instrument, platform, model counts
        Derived dataset (from CMR) counts
    
    For each sentence:
        Extract instruments, platforms or models (either GES DISC or not) record them as matching instrument/platform pair if possible, otherwise as single features.
        Extract science keywords, and record them.
    For each instrument/platform pair:
        For each science keyword:
            Query CMR and record first returned dataset
    For reminder of instruments
        For each science keyword:
            Query CMR and record first returned dataset
            
            
    I want to add spatial resolutions, level, versions, etc.. if possible
}

'''

if __name__ == '__main__':
    preprocess_location = ''
    zot_linkage_location = '../more_papers_data/zot_linkage/'
    dataset_couples_location = '../data/json/datasets_to_couples.json'

    key_title_ground_truth = get_manually_reviewed_ground_truths(zot_linkage_location, dataset_couples_location)
    sentences_stats_queries = run_keyword_sentences()

    now = datetime.now()
    current_time = now.strftime("%H-%M-%S")

    with open(current_time + 'key_title_ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(key_title_ground_truth, f, indent=4)

    with open(current_time + 'features.json', 'w', encoding='utf-8') as f:
        json.dump(sentences_stats_queries, f, indent=4)

    # iterate through the manually reviewed ones. Insert it into the paper applicable if possible
    for parent_key, value in key_title_ground_truth.items():
        pdf_key = value['pdf']
        if pdf_key in sentences_stats_queries:
            for inner_key, inner_value in sentences_stats_queries[pdf_key].items():
                value[inner_key] = inner_value

        key_title_ground_truth[parent_key] = value

    with open(current_time + 'features_merged.json', 'w', encoding='utf-8') as f:
        json.dump(key_title_ground_truth, f, indent=4)


'''
 @todo: currently the key for the sentences is ../covert_using_cerm.../...txt so keys are not matching up
'''