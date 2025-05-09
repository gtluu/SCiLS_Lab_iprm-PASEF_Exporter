import argparse
from scilslab import LocalSession


def get_args():
    """
    Parse command line parameters.

    :return: Arguments with default or user specified values.
    :rtype: dict
    """
    parser = argparse.ArgumentParser()
    # General parameters
    parser.add_argument('--scils',
                        help='Path to SCiLS .slx file.',
                        required=True,
                        type=str)

    arguments = parser.parse_args()
    return vars(arguments)


def get_feature_list_ids(slx):
    """
    Get the feature list IDs in a given SCiLS Lab file. Used to obtain feature list IDs for iprm-PASEF Precursor
    Scheduler and iprm-PASEF MS/MS to MGF workflows.

    :param slx:
    :return:
    """
    with LocalSession(filename=slx) as session:
        dataset = session.dataset_proxy
        feature_lists = dataset.feature_table.get_feature_lists()
        print(feature_lists)


def main():
    """
    Run workflow.
    """
    args = get_args()
    get_feature_list_ids(args['scils'])
