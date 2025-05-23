from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
475729
455868
640253
1050494
1067699
554736
649899
632038
501670
302261
511152
314649
637857
350234
136494
405848
481481
568070
628539
627898
628555
627899
611650
323666
363848
454278
559716
629252
626487
400002
208092
253199
382596
418600
565616
222458
611674
636531
553350
614593
651407
1073166
1072545
527360
1048988
432479
1015415
621913
644757
620231
613947
530531
474397
472914
644774
553396
648263
521255
1051832
96753
504833
498691
78207
451610
480138
509442
317091
509256
510811
454826
467110
39509
512871
224412
508141
181481
221659
479374
377532
100829
481979
478542
516839
377532
230598
389479
522433
527120
528296
530547
71446
390353
529481
543991
545887
501417
551279
552481
452212
554471
552522
476704
553046
562828
562854
563770
504913
551887
298716
568349
566249
408184
70110
570589
568731
424838
15657
368636
180045
575929
586481
582589
545463
2383
589754
589755
298716
584491
564450
98384
588281
346821
586558
187422
525175
601875
601871
605941
605941
450021
616318
620808
530547
625795
607341
626555
638494
638495
644774
579071
648474
123447
1018902
1019291
203947
472952
229859
1030B43
1033503
1038956
129674
620808
618748
1052716
1054808
1060170
525198
2062501
136814
10678
420028
208971
1067702
94485
1069106
392325
1078526
1090678
1068594
1128556
199547
1101741
1137716
1166841
282516

'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
