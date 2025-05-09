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
    parser.add_argument('--feature_list_id',
                        help='UUID for the MS1 feature table of interest. If unknown, please run the '
                             '"get_feature_lists" command.',
                        required=True,
                        type=str)

    arguments = parser.parse_args()
    return vars(arguments)


def get_intensity_column_names(slx, feature_list_id):
    """
    Get the column names for a given SCiLS Lab feature list. Used to obtain intensity column names for iprm-PASEF
    Precursor Scheduler workflow.

    :param slx:
    :param feature_list_id:
    :return:
    """
    with LocalSession(filename=slx) as session:
        dataset = session.dataset_proxy
        feature_list = dataset.feature_table.get_features(feature_list_id, include_all_user_columns=True)
        print(feature_list.columns)


def main():
    """
    Run workflow.
    """
    args = get_args()
    get_intensity_column_names(args['scils'], args['feature_list_id'])
