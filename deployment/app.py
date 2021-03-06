from flask import Flask, request, redirect, url_for,render_template
import pathlib
import tensorflow as tf
import cv2
import argparse
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import warnings
import glob
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # Suppress TensorFlow logging (1)

warnings.filterwarnings('ignore') 
# Suppress Matplotlib warnings

# Enable GPU dynamic memory allocation
import time
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils

gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)  
    
#pytesseract   
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# trained model_path
PATH_TO_MODEL_DIR = 'C:/Users/MYTHRY/Desktop/poc2/Invoice/fast2/exported-models/my_model'
#test_image_path    
#IMAGE_PATHS = 'C:/Users/MYTHRY/Desktop/poc2/Invoice/fast2/images/Train/0_7175.pdf.jpg'
# PROVIDE PATH TO LABEL MAP
PATH_TO_LABELS = 'C:/Users/MYTHRY/Desktop/poc2/Invoice/fast2/Annotation/label_map.pbtxt'

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('index.html')
        
@app.route('/submit', methods=['GET', 'POST'])  
def prediction_invoice():
    if request.method == 'POST':
        f = request.files['filename']
     
        f.save('static/test_image/'+f.filename)
        IMAGE_PATHS='static/test_image/'+f.filename 
        result1=model_prediction(IMAGE_PATHS,PATH_TO_LABELS,PATH_TO_MODEL_DIR)
        print(result1)
        f=open("static/text_data/result.txt","a");
        f.write(str(result1))
        #1:Invoice Date #2:Invoice Number #3.Total#4.Bill_from #5.Bill_to
        
        try:
            resulta=result1[1]
            resultb=result1[2]
            resultc=result1[3]
            resultd=result1[4]
            resulte=result1[5]
        except KeyError as e:
            pass
            
        for key in (1,2,3,4,5):
            if key not in result1:
                result1[key] = ' '
        
            
            
    return render_template("result.html",result="static/FaterRcnn_prediction/1.jpg",resulta=result1[1],resultb=result1[2],resultc=result1[3],resultd=result1[4],resulte=result1[5])
   #resulta=result1[1]
  

    
def model_prediction(IMAGE_PATHS,PATH_TO_LABELS,PATH_TO_MODEL_DIR):

    # PROVIDE THE MINIMUM CONFIDENCE THRESHOLD
    MIN_CONF_THRESH = float(0.60)
    #load the model
    PATH_TO_SAVED_MODEL = PATH_TO_MODEL_DIR + "/saved_model"
    print('Loading model...', end='')
    start_time = time.time()
    # LOAD SAVED MODEL AND BUILD DETECTION FUNCTION
    detect_fn = tf.saved_model.load(PATH_TO_SAVED_MODEL)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print('Done! Took {} seconds'.format(elapsed_time))
    # LOAD LABEL MAP DATA FOR PLOTTING
    category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS,
                                                                        use_display_name=True)
    def load_image_into_numpy_array(path):
        
        return np.array(Image.open(path))

    print('Running inference for {}... '.format(IMAGE_PATHS), end='')


    image = cv2.imread(IMAGE_PATHS)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_expanded = np.expand_dims(image_rgb, axis=0)
    # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
    input_tensor = tf.convert_to_tensor(image)
    # The model expects a batch of images, so add an axis with `tf.newaxis`.
    input_tensor = input_tensor[tf.newaxis, ...]
    # input_tensor = np.expand_dims(image_np, 0)
    detections = detect_fn(input_tensor)
    # All outputs are batches tensors.
    # Convert to numpy arrays, and take index [0] to remove the batch dimension.
    # We're only interested in the first num_detections.
    num_detections = int(detections.pop('num_detections'))
    detections = {key: value[0, :num_detections].numpy()
                   for key, value in detections.items()}
    detections['num_detections'] = num_detections

    # detection_classes should be ints.
    detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

    image_with_detections = image.copy()

    # SET MIN_SCORE_THRESH BASED ON YOU MINIMUM THRESHOLD FOR DETECTIONS
    viz_utils.visualize_boxes_and_labels_on_image_array(
          image_with_detections,
          detections['detection_boxes'],
          detections['detection_classes'],
          detections['detection_scores'],
          category_index,
          use_normalized_coordinates=True,
          max_boxes_to_draw=200,
          min_score_thresh=0.5,
          agnostic_mode=False)

    print('Done')
    # DISPLAYS OUTPUT IMAGE
    #cv2.imshow(image_with_detections,IMAGE_PATHS)
    plt.imshow(image_with_detections)
    output_dir = "static/FaterRcnn_prediction/"
    cv2.imwrite(output_dir  + "1.jpg", image_with_detections)
    #plt.savefig(output_dir  + "1.jpg")
    result_text=text_extraction(detections,image)
    return result_text
    
def text_extraction(detections,image):
    data=detections['detection_scores']
    t=np.where(data>0.6)
    #print(detections['detection_scores'][t])
    #print(detections['detection_boxes'][t])
    dete_box=detections['detection_boxes'][t]
    #le=len(dete_box)
    #ymin,xmin,ymax,xmax
    det_cla=detections['detection_classes'][t]
    #1:Invoice Date #2:Invoice Number #3.Total#4.Bill_from #5.Bill_to
    #results_dir=r'C:\Users\MYTHRY\Desktop\poc2\Invoice\fast2\static\Cropped_image'
    (frame_height, frame_width) = image.shape[:2]
    c = 0
    for i in dete_box.tolist():
    #print(i)
        ymin = int((i[0]*frame_height))
        xmin = int((i[1]*frame_width))
        ymax = int((i[2]*frame_height))
        xmax = int((i[3]*frame_width))
        crop_img = image[ymin:ymax,xmin:xmax]
        #plt.imshow((crop_img))
        #to save croped image
        cv2.imwrite(f'static/Cropped_image/image_{c}.png'.format(c),crop_img)
        c+=1
      
        #text extraction
        text=[]
        cv_img = []
        for img in glob.glob(r"static/Cropped_image/*.png"):
            text_img= cv2.imread(img)
            #print(text_img)
            text1 = pytesseract.image_to_string(text_img)
            #print(text1)
            text.append(text1)
            
    dict_from_list = {k: v for k, v in zip(det_cla, text)}
    #print(dict_from_list)
    return dict_from_list

   #debug=True

   
if __name__ == "__main__":
    app.run(host='0.0.0.0',port='3000')


