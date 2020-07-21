import xml.etree.ElementTree as ET
import os
import json

coco = dict()
coco['images'] = []
coco['type'] = 'instances'
coco['annotations'] = []
coco['categories'] = []

category_set = dict()
image_set = set()

category_item_id = 0
image_id = 20180000000
annotation_id = 0

def addCatItem(name):
    global category_item_id
    category_item = dict()
    category_item['supercategory'] = 'none'
    category_item_id += 1
    category_item['id'] = category_item_id
    category_item['name'] = name
    coco['categories'].append(category_item)
    category_set[name] = category_item_id
    return category_item_id

def addImgItem(file_name, size):
    global image_id
    if file_name is None:
        raise Exception('Could not find filename tag in xml file.')
    if size['width'] is None:
        raise Exception('Could not find width tag in xml file.')
    if size['height'] is None:
        raise Exception('Could not find height tag in xml file.')
    image_id += 1
    image_item = dict()
    image_item['id'] = image_id
    image_item['file_name'] = file_name
    image_item['width'] = size['width']
    image_item['height'] = size['height']
    coco['images'].append(image_item)
    image_set.add(file_name)
    return image_id

def addAnnoItem(object_name, image_id, category_id, bbox):
    global annotation_id
    annotation_item = dict()
    annotation_item['segmentation'] = []
    seg = []
    #bbox[] is x,y,w,h
    #left_top
    seg.append(bbox[0])
    seg.append(bbox[1])
    #left_bottom
    seg.append(bbox[0])
    seg.append(bbox[1] + bbox[3])
    #right_bottom
    seg.append(bbox[0] + bbox[2])
    seg.append(bbox[1] + bbox[3])
    #right_top
    seg.append(bbox[0] + bbox[2])
    seg.append(bbox[1])

    annotation_item['segmentation'].append(seg)

    annotation_item['area'] = bbox[2] * bbox[3]
    annotation_item['iscrowd'] = 0
    annotation_item['ignore'] = 0
    annotation_item['image_id'] = image_id
    annotation_item['bbox'] = bbox
    annotation_item['category_id'] = category_id
    annotation_id += 1
    annotation_item['id'] = annotation_id
    coco['annotations'].append(annotation_item)

def parseXmlFiles(xml_path): 
    for f in os.listdir(xml_path):
        if not f.endswith('.xml'):
            continue
        
        bndbox = dict()
        size = dict()
        current_image_id = None
        current_category_id = None
        file_name = None
        size['width'] = None
        size['height'] = None
        size['depth'] = None

        xml_file = os.path.join(xml_path, f)
        print(xml_file)

        tree = ET.parse(xml_file)
        root = tree.getroot()
        if root.tag != 'annotation':
            raise Exception('pascal voc xml root element should be annotation, rather than {}'.format(root.tag))

        #elem is <folder>, <filename>, <size>, <object> 
        current_parent = 'filename'
        current_sub = None
        object_name = None
        for elem in root:
            if elem.tag == current_parent:
                file_name = elem.text
                if file_name in category_set:
                    raise Exception('file_name duplicated')
        
        # size
        current_parent = 'size'
        current_sub = None
        object_name = None
        for elem in root:
            if elem.tag == current_parent:
                for subelem in elem:
                    current_sub = subelem.tag
                    if size[current_sub] is not None:
                        raise Exception('xml structure broken at size tag.')
                    size[current_sub] = int(subelem.text)

        #add img item only after parse <size> tag
        if current_image_id is None and file_name is not None and size['width'] is not None:
            current_sub = None
            object_name = None
            for elem in root:
                if elem.tag == current_parent:
                    if file_name not in image_set:
                        current_image_id = addImgItem(file_name, size)
                        print('add image with {} and {}'.format(file_name, size))
                    else:
                        raise Exception('duplicated image: {}'.format(file_name)) 

        # object
        current_parent = 'object'
        current_sub = None
        object_name = None
        for elem in root:
            if elem.tag == current_parent:
                for subelem in elem:
                    current_sub = subelem.tag
                    bndbox ['xmin'] = None
                    bndbox ['xmax'] = None
                    bndbox ['ymin'] = None
                    bndbox ['ymax'] = None
                    
                    if current_sub == 'name':
                        object_name = subelem.text
                        if object_name not in category_set:
                            current_category_id = addCatItem(object_name)
                        else:
                            current_category_id = category_set[object_name]

                    #option is <xmin>, <ymin>, <xmax>, <ymax>, when subelem is <bndbox>
                    if current_sub == 'bndbox':
                        for option in subelem:
                            if bndbox[option.tag] is not None:
                                raise Exception('xml structure corrupted at bndbox tag.')
                            bndbox[option.tag] = int(option.text)

                    #only after parse the <object> tag
                    if bndbox['xmin'] is not None:
                        if object_name is None:
                            raise Exception('xml structure broken at bndbox tag')
                        if current_image_id is None:
                            raise Exception('xml structure broken at bndbox tag')
                        if current_category_id is None:
                            raise Exception('xml structure broken at bndbox tag')
                        bbox = []
                        bbox.append(bndbox['xmin'])
                        bbox.append(bndbox['ymin'])
                        bbox.append(bndbox['xmax'] - bndbox['xmin'])
                        bbox.append(bndbox['ymax'] - bndbox['ymin'])

                        print('add annotation with {},{},{},{}'.format(object_name, current_image_id, current_category_id, bbox))
                        addAnnoItem(object_name, current_image_id, current_category_id, bbox )

if __name__ == '__main__':
    xml_path = 'datasets/voc_2010/VOCdevkit/VOC2010/Annotations'
    json_file = 'datasets/voc_2010/VOCdevkit/VOC2010/voc2010_instances_all.json'
    parseXmlFiles(xml_path)
    json.dump(coco, open(json_file, 'w'))