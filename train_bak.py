import warnings

warnings.filterwarnings("ignore")

import os
import yaml

from dotmap import DotMap
import torch
from ptflops import get_model_complexity_info

from experiment_bak import Exp

seeds = [10]
models = [ #"tinyhar", "sahar", 
    "deepconvlstm",]  # ["sahar", "deepconvlstm_attn", "mcnn", "tinyhar", "deepconvlstm", "attend"]
datasets = ["pamap2",
            #"rw", "uschad"]  # ["dg", "uschad", "pamap2", "rw", "skodar", "dsads", "hapt", "oppo", "wisdm"]
            ]
for ds in datasets:
    for m in models:
        for seed in seeds:
            args = DotMap()
            args.to_save_path = "Run_logs"
            args.freq_save_path = "Freq_data"
            args.stats_save_path = "Stats_data"
            args.window_save_path = "Sliding_window"
            args.root_path = "datasets"

            args.drop_transition = False
            args.datanorm_type = "standardization"  # None ,"standardization", "minmax"

            args.batch_size = 256
            args.shuffle = True
            args.drop_last = False
            args.train_vali_quote = 0.90

            # training setting
            args.train_epochs = 150

            args.learning_rate = 0.0001  # 0.001
            args.learning_rate_patience = 7
            args.learning_rate_factor = 0.1

            args.early_stop_patience = 15

            args.use_gpu = True if torch.cuda.is_available() else False
            args.gpu = 0
            args.use_multi_gpu = False

            args.optimizer = "Adam"
            args.criterion = "CrossEntropy"
            args.data_name = ds
            args.model_type = m
            args.seed = seed
            args.wavelet_filtering = False
            args.wavelet_filtering_regularization = False
            args.wavelet_filtering_finetuning = False
            args.wavelet_filtering_finetuning_percent = 0.5
            args.wavelet_filtering_learnable = False
            args.wavelet_filtering_layernorm = False
            args.regulatization_tradeoff = 0
            args.number_wavelet_filtering = 12
            args.difference = False
            args.filtering = False
            args.magnitude = False
            args.weighted_sampler = False
            args.pos_select = None
            args.sensor_select = ["acc"] #gyro
            args.representation_type = "time"   # time, freq, time_freq, time_stats
            args.exp_mode = "LOCV"
            if args.data_name == "skodar":
                args.exp_mode = "SOCV"
            config_file = open('configs/data.yaml', mode='r')
            data_config = yaml.load(config_file, Loader=yaml.FullLoader)
            config = data_config[args.data_name]

            args.root_path = os.path.join(args.root_path, config["filename"])
            args.sampling_freq = config["sampling_freq"]
            args.num_classes = config["num_classes"]
            window_seconds = config["window_seconds"]
            args.windowsize = int(window_seconds * args.sampling_freq)
            args.input_length = args.windowsize
            # input information
            args.c_in = config["num_channels"]

            if args.difference:
                args.c_in = args.c_in * 2

            if args.wavelet_filtering:
                if args.windowsize % 2 == 1:
                    N_ds = int(torch.log2(torch.tensor(args.windowsize - 1)).floor()) - 2
                else:
                    N_ds = int(torch.log2(torch.tensor(args.windowsize)).floor()) - 2

                args.f_in = args.number_wavelet_filtering * N_ds + 1
            else:
                args.f_in = 1

            if args.model_type == 'tinyhar':
                args.cross_channel_interaction_type = "attn"
                args.cross_channel_aggregation_type = "FC"
                args.temporal_info_interaction_type = "lstm"
                args.temporal_info_aggregation_type = "tnaive"

            # added - SY Baek
            args.filter_scaling_factor = 1

            exp = Exp(args)

            macs, params = get_model_complexity_info(exp.model, (1, args.input_length, args.c_in), as_strings=False, print_per_layer_stat=True, verbose=False)
            print('macs', macs)
            print('{:<30}  {:<8}'.format('Computational complexity: ', macs))
            print('{:<30}  {:<8}'.format('Number of parameters: ', params))
            exp.train()
