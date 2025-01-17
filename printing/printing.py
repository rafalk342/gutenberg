# Original script by zielmicha (https://github.com/zielmicha)

import shutil
import subprocess
import tempfile

import os

from django.conf import settings

DOCUMENT_FORMATS = ('doc', 'docx', 'rtf', 'odt')
IMAGE_FORMATS = ('png', 'jpg', 'jpeg')
PDF_FORMAT = ('pdf',)
SUPPORTED_FILE_FORMATS = DOCUMENT_FORMATS + IMAGE_FORMATS + PDF_FORMAT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_PATH = os.path.join(BASE_DIR, 'sandbox.sh')

CONVERT_OPTIONS = [
    '-resize', '2365x3335', '-gravity', 'center', '-background', 'white',
    '-extent', '2490x3510', '-units', 'PixelsPerInch', '-density', '300x300'
]

TWO_SIDED_DISABLED = 'None'
TWO_SIDED_LONG_EDGE = 'LongEdge'
TWO_SIDED_SHORT_EDGE = 'ShortEdge'


def convert_to_pdf(filename):
    tmpdir = tempfile.mkdtemp()
    ext = filename.lower().rsplit('.', 1)[-1]

    is_image = ext in IMAGE_FORMATS
    is_doc = ext in DOCUMENT_FORMATS
    is_pdf = ext in PDF_FORMAT

    tmpname = tmpdir + '/in.' + ext
    shutil.copy(filename, tmpname)

    if is_image:
        out = tmpdir + '/out.pdf'
        subprocess.check_call(
            [SANDBOX_PATH, tmpdir, 'convert', tmpname] + CONVERT_OPTIONS +
            [out])
    elif is_pdf:
        out = tmpname
    elif is_doc:
        out = tmpdir + '/out.pdf'
        subprocess.check_call(
            [SANDBOX_PATH, tmpdir, 'unoconv', '-o', out, tmpname])
    else:
        raise ValueError()

    subprocess.check_call(
        [SANDBOX_PATH, tmpdir, 'gs', '-sDEVICE=pdfwrite', '-dNOPAUSE',
         '-dBATCH', '-dSAFER', '-dCompatibilityLevel=1.4',
         '-sOutputFile=' + tmpdir + '/final.pdf', out])

    return tmpdir + '/final.pdf', lambda: shutil.rmtree(tmpdir)


def generate_hp500_options(copy_number: int, pages_to_print: str,
                           color_enabled: bool, two_sided: str):
    options = []
    options += ['-n', str(copy_number)]
    if pages_to_print:
        options += ['-P', pages_to_print]
    options += ['-o', 'HPColorAsGray={}'.format(not color_enabled)]

    two_sided_opt = {
        TWO_SIDED_DISABLED: 'None',
        TWO_SIDED_LONG_EDGE: 'DuplexNoTumble',
        TWO_SIDED_SHORT_EDGE: 'DuplexTumble',
    }[two_sided]
    options += ['-o', 'Duplex={}'.format(two_sided_opt)]
    options += ['-o', 'fit-to-page']
    return options


generate_options = generate_hp500_options


def print_file(file_path, **options):
    out, cleanup = convert_to_pdf(file_path)
    subprocess.check_call(
        ['lp', out] + ['-d', settings.PRINTER_NAME] +
        generate_options(**options))
    cleanup()
