# -*- coding: utf-8 -*-
# Copyright 2017 Kakao, Recommendation Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import tensorflow as tf

import keras
from keras.models import Model
from keras.layers.merge import dot
from keras.layers import Dense, Input, concatenate, BatchNormalization, CuDNNGRU
from keras.layers.core import Reshape

from keras.layers.embeddings import Embedding
from keras.layers.core import Dropout, Activation

from functools import partial, update_wrapper
from metric import fbeta_score_macro, arena_score
from misc import get_logger, Option, ModelMGPU
opt = Option('./config.json')


def top1_acc(x, y):
    return keras.metrics.top_k_categorical_accuracy(x, y, k=1)


class TextOnly:
    def __init__(self):
        self.logger = get_logger('textonly')

    def get_model(self, num_classes, activation='sigmoid'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        with tf.device('/gpu:0'):
            embd = Embedding(voca_size,
                             opt.embd_size,
                             name='uni_embd')

            t_uni = Input((max_len,), name="input_1")
            t_uni_embd = embd(t_uni)  # token

            w_uni = Input((max_len,), name="input_2")
            w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

            uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
            uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)

            embd_out = Dropout(rate=0.5)(uni_embd)
            relu = Activation('relu', name='relu1')(embd_out)
            outputs = Dense(num_classes, activation=activation)(relu)
            model = Model(inputs=[t_uni, w_uni], outputs=outputs)
            optm = keras.optimizers.Nadam(opt.lr)
            model.compile(loss='binary_crossentropy',
                        optimizer=optm,
                        metrics=[top1_acc])
            model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextImage:
    def __init__(self, vocab_matrix=None):
        self.logger = get_logger('text_img')
        self.vocab = vocab_matrix

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        # image feature
        img = Input((opt.img_size,), name="input_3")

        uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        img_feat = Reshape((opt.img_size, ))(img)
        pair = concatenate([uni_embd, img_feat])
        embd_out = BatchNormalization()(pair)
        relu = Activation('relu', name='relu1')(embd_out)
        outputs = Dense(num_classes, activation=activation)(relu)
        model = Model(inputs=[t_uni, w_uni, img], outputs=outputs)
        if opt.num_gpus > 1:
            model = ModelMGPU(model, gpus=opt.num_gpus)
        optm = keras.optimizers.Nadam(opt.lr)
        metrics = [top1_acc, fbeta_score_macro]

        # metric for kakao arena
        arena_score_metric = update_wrapper(partial(arena_score,
                                            vocab_matrix=self.vocab),
                                            arena_score)
        metrics += [arena_score_metric] if self.vocab is not None else []

        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=metrics)
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextB:
    def __init__(self, vocab_matrix=None):
        self.logger = get_logger('text_b')
        self.vocab = vocab_matrix

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight


        uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        embd_out = Dropout(rate=0.5)(uni_embd)
        relu = Activation('relu', name='relu1')(embd_out)
        outputs = Dense(num_classes, activation=activation)(relu)
        model = Model(inputs=[t_uni, w_uni], outputs=outputs)
        if opt.num_gpus > 1:
            model = ModelMGPU(model, gpus=opt.num_gpus)
        optm = keras.optimizers.Nadam(opt.lr)
        metrics = [top1_acc, fbeta_score_macro]

        # metric for kakao arena
        arena_score_metric = update_wrapper(partial(arena_score,
                                            vocab_matrix=self.vocab),
                                            arena_score)
        metrics += [arena_score_metric] if self.vocab is not None else []

        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=metrics)
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextM:
    def __init__(self, vocab_matrix=None):
        self.logger = get_logger('text_m')
        self.vocab = vocab_matrix

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        b_in = Input((1,), name="input_b")

        uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        pair = concatenate([uni_embd, b_in])
        embd_out = Dropout(rate=0.5)(pair)
        relu = Activation('relu', name='relu1')(embd_out)
        outputs = Dense(num_classes, activation=activation)(relu)
        model = Model(inputs=[t_uni, w_uni, b_in], outputs=outputs)
        if opt.num_gpus > 1:
            model = ModelMGPU(model, gpus=opt.num_gpus)
        optm = keras.optimizers.Nadam(opt.lr)
        metrics = [top1_acc, fbeta_score_macro]

        # metric for kakao arena
        arena_score_metric = update_wrapper(partial(arena_score,
                                            vocab_matrix=self.vocab),
                                            arena_score)
        metrics += [arena_score_metric] if self.vocab is not None else []

        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=metrics)
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextBMSD:
    def __init__(self, vocab_matrix=None):
        self.logger = get_logger('text_bmsd')
        self.vocab = vocab_matrix

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1
        # image feature
        img = Input((opt.img_size,), name="input_3")
        img_feat = Reshape((opt.img_size, ))(img)

        # b cate
        embd_b = Embedding(voca_size,
                         opt.embd_size,
                         name='b_embd')

        t_uni = Input((max_len,), name="input_1")
        b_embd = embd_b(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        uni_embd_mat = dot([b_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        pair = concatenate([uni_embd, img_feat])
        embd_out = BatchNormalization()(pair)
        relu = Activation('relu', name='relu1')(embd_out)
        b_out = Dense(num_classes['b'], activation=activation)(relu)

        # m cate
        b_in = Input((1,), name="input_b")
        embd_m = Embedding(voca_size,
                           opt.embd_size,
                           name='m_embd')
        m_embd = embd_m(t_uni)  # token
        m_uni_embd_mat = dot([m_embd, w_uni_mat], axes=1)
        m_uni_embd = Reshape((opt.embd_size, ))(m_uni_embd_mat)
        m_pair = concatenate([m_uni_embd, b_in, img_feat])
        m_embd_out = BatchNormalization()(m_pair)
        m_relu = Activation('relu', name='relu2')(m_embd_out)
        m_out = Dense(num_classes['m'], activation=activation)(m_relu)

        # s cate
        m_in = Input((1,), name="input_m")
        embd_s = Embedding(voca_size,
                           opt.embd_size,
                           name='s_embd')
        s_embd = embd_s(t_uni)  # token
        s_uni_embd_mat = dot([s_embd, w_uni_mat], axes=1)
        s_uni_embd = Reshape((opt.embd_size, ))(s_uni_embd_mat)

        bm_in = Input((2,), name="input_bm")
        embd_bm_seq = Embedding(num_classes['b'] + num_classes['m'],
                                opt.embd_size,
                                name='bm_embd_seq')(bm_in)
        bm_seq_gru = CuDNNGRU(opt.embd_size // 2)(embd_bm_seq)
        s_pair = concatenate([s_uni_embd, bm_seq_gru, img_feat])
        s_embd_out = BatchNormalization()(s_pair)
        s_relu = Activation('relu', name='relu3')(s_embd_out)
        s_out = Dense(num_classes['s'], activation=activation)(s_relu)

        # d cate
        s_in = Input((1,), name="input_s")
        embd_d = Embedding(voca_size,
                           opt.embd_size,
                           name='m_embd')
        d_embd = embd_m(t_uni)  # token
        d_uni_embd_mat = dot([d_embd, w_uni_mat], axes=1)
        d_uni_embd = Reshape((opt.embd_size, ))(d_uni_embd_mat)

        bms_in = Input((3,), name="input_bms")
        embd_bms_seq = Embedding(num_classes['b'] + num_classes['m'] + num_classes['s'],
                                 opt.embd_size,
                                 name='bms_embd_seq')(bms_in)
        bms_seq_gru = CuDNNGRU(opt.embd_size // 2)(embd_bms_seq)
        d_pair = concatenate([d_uni_embd, bms_seq_gru, img_feat])
        d_embd_out = BatchNormalization()(d_pair)
        d_relu = Activation('relu', name='relu4')(d_embd_out)
        d_out = Dense(num_classes['d'], activation=activation)(d_relu)


        model = Model(inputs=[t_uni, w_uni, img, b_in, bm_in, bms_in], outputs=[b_out, m_out, s_out, d_out])
        if opt.num_gpus > 1:
            model = ModelMGPU(model, gpus=opt.num_gpus)
        optm = keras.optimizers.Nadam(opt.lr)
        metrics = [top1_acc, fbeta_score_macro]

        # metric for kakao arena
        arena_score_metric = update_wrapper(partial(arena_score,
                                            vocab_matrix=self.vocab),
                                            arena_score)
        metrics += [arena_score_metric] if self.vocab is not None else []

        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=metrics)
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model



class TextImageNN:
    def __init__(self):
        self.logger = get_logger('text_img_nn')

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        # image feature
        img = Input((opt.img_size,), name="input_3")

        uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        img_feat = Reshape((opt.img_size, ))(img)
        pair = concatenate([uni_embd, img_feat])
        x = Dropout(rate=0.5)(pair)
        x = Dense(opt.hidden_size, activation='relu')(x)
        x = Dropout(rate=0.5)(x)
        x = Dense(opt.hidden_size // 2, activation='relu')(x)
        x = Dropout(rate=0.5)(x)
        outputs = Dense(num_classes, activation=activation)(x)
        model = Model(inputs=[t_uni, w_uni, img], outputs=outputs)
        if opt.num_gpus > 1:
            model = ModelMGPU(model, gpus=opt.num_gpus)
        optm = keras.optimizers.Nadam(opt.lr)
        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=[top1_acc])
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextImagePrice:
    def __init__(self):
        self.logger = get_logger('text_img_price')

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        # image feature
        img = Input((opt.img_size,), name="input_3")

        # price feature
        price = Input((1,), name="input_4")

        uni_embd_mat = dot([t_uni_embd, w_uni_mat], axes=1)
        uni_embd = Reshape((opt.embd_size, ))(uni_embd_mat)
        img_feat = Reshape((opt.img_size, ))(img)
        price_feat = Reshape((1, ))(price)
        pair = concatenate([uni_embd, img_feat, price_feat])
        embd_out = Dropout(rate=0.5)(pair)
        relu = Activation('relu', name='relu1')(embd_out)
        outputs = Dense(num_classes, activation=activation)(relu)
        model = Model(inputs=[t_uni, w_uni, img, price], outputs=outputs)
        optm = keras.optimizers.Nadam(opt.lr)
        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=[top1_acc])
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model


class TextImagePriceNN:
    def __init__(self):
        self.logger = get_logger('text_img_price_nn')

    def get_model(self, num_classes, activation='softmax'):
        max_len = opt.max_len
        hidden_size = opt.hidden_size
        voca_size = opt.unigram_hash_size + 1

        embd = Embedding(voca_size,
                         opt.embd_size,
                         name='uni_embd')

        t_uni = Input((max_len,), name="input_1")
        t_uni_embd = embd(t_uni)  # token

        w_uni = Input((max_len,), name="input_2")
        w_uni_mat = Reshape((max_len, 1))(w_uni)  # weight

        # image feature
        img = Input((opt.img_size,), name="input_3")

        # price feature
        price = Input((1,), name="input_4")

        text_embd = dot([t_uni_embd, w_uni_mat], axes=1)
        text_embd = Reshape((opt.embd_size, ))(text_embd)
        img_feat = Reshape((opt.img_size, ))(img)
        price_feat = Reshape((1, ))(price)
        x = concatenate([text_embd, img_feat, price_feat])
        x = Dropout(rate=0.5)(x)
        x = Dense(hidden_size, activation='relu')(x)
        x = Dropout(rate=0.5)(x)
        x = Dense(hidden_size // 2, activation='relu')(x)
        x = Dropout(rate=0.5)(x)
        outputs = Dense(num_classes, activation=activation)(x)
        model = Model(inputs=[t_uni, w_uni, img, price], outputs=outputs)
        optm = keras.optimizers.Nadam(opt.lr)
        model.compile(loss='categorical_crossentropy',
                    optimizer=optm,
                    metrics=[top1_acc])
        model.summary(print_fn=lambda x: self.logger.info(x))
        return model
