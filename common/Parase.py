#encoding=utf-8
from bs4 import BeautifulSoup
import urllib
import re
import os
import Common
import numpy as np
from PIL import Image
from StringIO import StringIO
import os
os.environ['GLOG_minloglevel'] = '2'
import caffe

def resize_image(data, sz=(256, 256)):
    """
    Resize image. Please use this resize logic for best results instead of the
    caffe, since it was used to generate training dataset
    :param str data:
        The image data
    :param sz tuple:
        The resized image dimensions
    :returns bytearray:
        A byte array with the resized image
    """
    img_data = str(data)
    im = Image.open(StringIO(img_data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=Image.BILINEAR)
    fh_im = StringIO()
    imr.save(fh_im, format='JPEG')
    fh_im.seek(0)
    return bytearray(fh_im.read())


def caffe_preprocess_and_compute(pimg, caffe_transformer=None, caffe_net=None,
                                 output_layers=None):
    """
    Run a Caffe network on an input image after preprocessing it to prepare
    it for Caffe.
    :param PIL.Image pimg:
        PIL image to be input into Caffe.
    :param caffe.Net caffe_net:
        A Caffe network with which to process pimg afrer preprocessing.
    :param list output_layers:
        A list of the names of the layers from caffe_net whose outputs are to
        to be returned.  If this is None, the default outputs for the network
        are returned.
    :return:
        Returns the requested outputs from the Caffe net.
    """
    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(StringIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = max((H - h) / 2, 0)
        w_off = max((W - w) / 2, 0)
        crop = image[h_off:h_off + h, w_off:w_off + w, :]
        transformed_image = caffe_transformer.preprocess('data', crop)
        transformed_image.shape = (1,) + transformed_image.shape

        input_name = caffe_net.inputs[0]
        all_outputs = caffe_net.forward_all(blobs=output_layers,
                                            **{input_name: transformed_image})

        outputs = all_outputs[output_layers[0]][0].astype(float)
        return outputs
    else:
        return []


class Parser():
    invalidword = []  #不健康词汇表
    alllen = float(len(invalidword))
    threshold = None
    InvalidWordThread = None

    def __init__(self, config):
        self.ThresHold = float(config.get('caffe', 'Threshold'))
        self.DetectorFile = config.get('caffe', 'DetectorFile')
        self.ModelDef = config.get('caffe', 'ModelDef')
        self.PreTrainedModel = config.get('caffe', 'PreTrainedModel')
        self.ValHead = 'NSFW score:'
        #image_data = open(sys.argv[1]).read()
        # Pre-load caffe model.
        self.nsfw_net = caffe.Net(self.ModelDef,  # pylint: disable=invalid-name
                                    self.PreTrainedModel, caffe.TEST)
        # Load transformer
        # Note that the parameters are hard-coded for best results
        self.caffe_transformer = caffe.io.Transformer({'data': self.nsfw_net.blobs['data'].data.shape})
        self.caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
        self.caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
        self.caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
        self.caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR
        self.common = Common.Common()
        self.InvalidWordThread = float(config.get('caffe', 'InvalidWordThread')) * float(len(Parser.invalidword))

    '''
        在网页文本中匹配不良词汇，数量超过设定的阈值则认为是不良网页
    '''
    @classmethod
    def IsInvalidPage(cls, content):
        cnt = 0
        for word in Parser.invalidword:
            if word in content:
                cnt += 1
                if cnt >= cls.InvalidWordThread:
                    return True
        return False

    '''
        基于caffe框架，利用NSWF模型判断图片的不良程度，超过设定的阈值则认为是不良图片
    '''
    def IsInvalidImg(self, content, contenttype, url, recurse = True):
        if contenttype == 'image/webp':
            content = Common.Common.ConvWebp2JPEG(content)
            if content == '':
                return False
        try:
            scores = caffe_preprocess_and_compute(content, caffe_transformer=self.caffe_transformer, caffe_net=self.nsfw_net, output_layers=['prob'])
        except Exception as e:
            print 'url: ' + url
            print 'contenttype: ' + contenttype
            if recurse:
                content = Common.Common.ConvWebp2JPEG(content)
                return (content != '' and self.IsInvalidImg(content, contenttype, url, False))
        # Scores is the array containing SFW / NSFW image probabilities, scores[1] indicates the NSFW probability
        # print 'caffe img:',image_data
        if 'scores' in dir() and len(scores) > 1 and scores[1] >= self.ThresHold:
            print str(scores[1])
            return True
        return False

    def ParaseContent(self, content):
        soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
        soup.encode('utf-8')

        # get title
        titletext = soup.select('title')
        if len(titletext):
            titletext = titletext[0].text.strip()
        else:
            titletext = ''
        titletext = titletext.replace('\n', '')

        # pre tack tga div with display:none attribute
        for div in soup.select('div'):
            if div.has_attr("style") and 'display:none' in div['style']:
                for p in div.select('p'):
                    p.name = 'aaaaa'
                    # print soup.prettify()

        # get main text
        maintext = ''
        for res in soup.select('div p'):
            text = res.text.replace('\n', '').replace('\r', '').replace(' ', '')
            if len(text) > 0 and Common.Common.is_uchar(text):
                maintext = maintext + text + '\n'

        return titletext, maintext
