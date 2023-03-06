from formatConversion.xml2Midi import xml2midi
from formatConversion.xml2Midi import utils


data_path = "../data/midi"
output_txt_path = "../data/output.txt"
test_file = "../data/musicxml/Henry Smith 1978 - Give Thanks.mxl"

def do_test():
    """Test a single file with debugging"""
    xml2midi.convert_batch([test_file], data_path, skip_existing=False)
    messages = utils.get_midi_messages(utils.get_dest_midi_path(test_file, data_path))
    utils.write_list(messages, output_txt_path)

if __name__ == "__main__":
    do_test()