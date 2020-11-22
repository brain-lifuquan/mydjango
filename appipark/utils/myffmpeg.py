from collections import namedtuple
from ffmpy3 import FFmpeg


def run_myffmpeg(dict_in, out_path):
    inputs_list = get_inputs_list(dict_in)
    filter_a = get_filter_expression(dict_in, inputs_list=inputs_list)
    dict_inputs = get_inputs_dict(dict_in, inputs_list)
    dict_outputs = get_outputs_dict(out_path, filter_a, dict_in['duration'])
    ff = FFmpeg(
        inputs=dict_inputs,
        outputs=dict_outputs
    )
    print(ff.cmd)
    ff.run()
    return ff.cmd


def get_inputs_list(dict_in):
    Input = namedtuple('Input', 'path type')
    inputs_list = []
    if dict_in['bg_image']:
        inputs_list.append(Input(path=dict_in['bg_image'], type='image'))
    for grp in dict_in['groups']:
        for inp in grp['inputs']:
            inputs_list.append(Input(path=inp['path'], type=inp['type']))
    inputs_list = list(set(inputs_list))
    return inputs_list


def get_inputs_dict(dict_in, inputs_list):
    dict_inputs = {}
    # if dict_in['bg_image']:
    #     dict_inputs[dict_in['bg_image']] = '-loop 1 -t {}'.format(dict_in['duration'])
    for inp in inputs_list:
        if inp.type == 'image':
            dict_inputs[inp.path] = '-loop 1 -t {}'.format(dict_in['duration'])
        elif inp.type == 'video':
            dict_inputs[inp.path] = None
    return dict_inputs


def get_outputs_dict(out_path, filter_expression, duration):
    dict_outputs = {
        out_path: '-filter_complex "{}" -t {} -y -loglevel error'.format(filter_expression, str(duration))
        # out_path: '-filter_complex "{}" -t {} -y'.format(filter_expression, str(duration))
    }
    return dict_outputs


def get_grp_filter(grp, grp_index, index_dict):
    # select 选择符合条件的帧  select 应用还有问题，后面再修改
    # scale_filter_fmt = r"[{index}:v]select=between(t\,0\,{end}),scale=width={width}:height={height}[{tag}]"
    scale_filter_fmt = r"[{index}:v]scale=width={width}:height={height}[{tag}]"
    # concat 滤镜 将不同的输入进行连接 参数 n 输入的数量，默认为2  unsafe: 开启非安全模式 不强制要求输入的格式一致
    concat_filter_fmt = r"{in_tags}concat=n={n}:unsafe=1[{out_tag}]"
    grp_size = grp['size']
    if len(grp['inputs']) > 1:
        grp_scales = []
        grp_input_tags = []
        for inp in grp['inputs']:
            input_path = inp['path']
            input_index = index_dict[input_path]
            input_type = inp['type']
            input_duration = inp['duration']
            scale_tag = 'scale{}'.format(input_index)
            grp_input_tags.append(scale_tag)
            # 使用scale滤镜将输入进行统一分辨率
            # scale_filter = scale_filter_fmt.format(index=input_index, width=grp_size['width'], height=grp_size['height'], tag=scale_tag, end=input_duration['start'] + input_duration['end'])
            scale_filter = scale_filter_fmt.format(index=input_index, width=grp_size['width'], height=grp_size['height'], tag=scale_tag)
            grp_scales.append(scale_filter)

        # 将每个视频连起来组成新视频流
        in_tags = '[{}]'.format(']['.join(grp_input_tags))
        out_tag = 'grp{}'.format(grp_index)
        grp_concat_filter = concat_filter_fmt.format(in_tags=in_tags, n=len(grp_input_tags), out_tag=out_tag)
        grp_filter = ';'.join(grp_scales) + ';' + grp_concat_filter

    else:
        # grp下只有1个元素 不需要concate
        inp = grp['inputs'][0]
        input_path = inp['path']
        input_index = index_dict[input_path]
        input_type = inp['type']
        input_duration = inp['duration']
        out_tag = 'grp{}'.format(grp_index)
        # 使用scale滤镜将输入进行统一分辨率
        # grp_filter = scale_filter_fmt.format(index=input_index, width=grp_size['width'], height=grp_size['height'], tag=out_tag, end=input_duration['start'] + input_duration['end'])
        grp_filter = scale_filter_fmt.format(index=input_index, width=grp_size['width'], height=grp_size['height'], tag=out_tag)
    return grp_filter


def get_overlay_filter(grp, grp_index, dict_in):
    overlay_filter_fmt = r"[{tag_in_1}][{tag_in_2}]overlay='x=if(between(t,{start},{end}),{left},NAN)':y={top}:repeatlast=0[{tag_out}]"
    overlay_tag = 'overlay{}'.format(grp_index)
    grp_duration = grp['duration']
    grp_position = grp['position']
    # 如果是第一个grp需要覆盖在base上
    if grp_index == 0:
        tag_in_1 = 'base'
    else:
        tag_in_1 = 'overlay{}'.format(grp_index - 1)
    tag_in_2 = 'grp{}'.format(grp_index)
    overlay_filter = overlay_filter_fmt.format(tag_in_1=tag_in_1, tag_in_2=tag_in_2, tag_out=overlay_tag,
                                               start=grp_duration['start'], end=grp_duration['end'],
                                               left=grp_position['left'], top=grp_position['top'])
    # 最后的一个要去掉tag
    if grp_index == len(dict_in['groups']) - 1:
        overlay_filter = overlay_filter.replace('[{}]'.format(overlay_tag), '')
    return overlay_filter


def get_filter_expression(dict_in, inputs_list):
    index_dict = {inp.path: index for index, inp in enumerate(inputs_list)}
    if dict_in['bg_image']:
        input_index = index_dict[dict_in['bg_image']]
        scale_base = "[{index}:v]scale=width={width}:height={height}[base]".format(index=input_index, width=dict_in['size']['width'], height=dict_in['size']['height'])
    else:
        scale_base = "nullsrc=size={width}x{height}[base]".format(width=dict_in['size']['width'], height=dict_in['size']['height'])

    concat_filter_fmt = r"{in_tags}concat=unsafe=1[{out_tag}]"
    overlay_filter_fmt = r"[{tag_in_1}][{tag_in_2}]overlay='x=if(between(t,{start},{end}),{left},NAN)':y={top}:repeatlast=0[{tag_out}]"

    overlays_filter = []
    grps_filter = []
    for grp_index, grp in enumerate(dict_in['groups']):
        grp_filter = get_grp_filter(grp, grp_index, index_dict)
        grps_filter.append(grp_filter)
        overlay_filter = get_overlay_filter(grp, grp_index, dict_in)
        overlays_filter.append(overlay_filter)
    # base
    filter_all = scale_base + ';'
    # grps
    filter_all += ';'.join(grps_filter) + ';'
    # overlays
    filter_all += ';'.join(overlays_filter)
    return filter_all


if __name__ == '__main__':
    dict_in = {
        # 画布
        'duration': 30,
        'size': {'width': 800, 'height': 600},
        'bg_image': None,
        # 位置
        'groups': [
            {
                'size': {'width': 300, 'height': 200},
                'position': {'left': 0, 'top': 0},
                'duration': {'start': 0, 'end': 30},
                'inputs': [
                    {
                        'path': 'a.mp4',
                        'type': 'video',
                        'duration': {'start': 0, 'end': 20}
                     },
                    {
                        'path': 'a.mp4',
                        'type': 'video',
                        'duration': {'start': 0, 'end': 10}
                    }
                ]
            },
            {
                'size': {'width': 300, 'height': 400},
                'position': {'left': 0, 'top': 200},
                'duration': {'start': 0, 'end': 30},
                'inputs': [
                    {
                        'path': '1.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                    {
                        'path': '2.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                ]
            },
            {
                'size': {'width': 500, 'height': 600},
                'position': {'left': 300, 'top': 0},
                'duration': {'start': 0, 'end': 20},
                'inputs': [
                    {
                        'path': '2.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                    {
                        'path': '2.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                ]
            }
        ]
    }
    dict_in2 = {
        # 画布
        'duration': 30,
        'size': {'width': 800, 'height': 600},
        'bg_image': None,
        # 位置
        'groups': [
            {
                'size': {'width': 300, 'height': 200},
                'position': {'left': 0, 'top': 0},
                'duration': {'start': 0, 'end': 30},
                'inputs': [
                    {
                        'path': 'a.mp4',
                        'type': 'video',
                        'duration': {'start': 0, 'end': 20}
                     }
                ]
            },
            {
                'size': {'width': 300, 'height': 400},
                'position': {'left': 0, 'top': 200},
                'duration': {'start': 0, 'end': 30},
                'inputs': [
                    {
                        'path': '1.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                    {
                        'path': '2.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                ]
            },
            {
                'size': {'width': 500, 'height': 600},
                'position': {'left': 300, 'top': 0},
                'duration': {'start': 0, 'end': 20},
                'inputs': [
                    {
                        'path': '2.jpg',
                        'type': 'image',
                        'duration': {'start': 0, 'end': 15}
                    },
                ]
            }
        ]
    }
    re = run_myffmpeg(dict_in2, 'out3.mp4')
    print(re)
