import torch
import torch.nn as nn
import torch.nn.functional as F


def _L2_loss_mean(x):
    return torch.mean(torch.sum(torch.pow(x, 2), dim=1, keepdim=False) / 2.)


class Embedding_based(nn.Module):

    def __init__(self, args, n_users, n_items, n_entities, n_relations):

        super(Embedding_based, self).__init__()

        self.inject_manner = args.inject_manner
        # 处理 concat 的嵌入方式
        if args.inject_manner == 0:
            self.trans = nn.Linear(args.embed_dim * 2, args.embed_dim)
            # self.activate = nn.ReLU()
        self.use_pretrain = args.use_pretrain

        self.n_users = n_users
        self.n_items = n_items
        self.n_entities = n_entities
        self.n_relations = n_relations

        self.KG_embedding_type = args.KG_embedding_type

        self.embed_dim = args.embed_dim
        self.relation_dim = args.relation_dim

        self.cf_l2loss_lambda = args.cf_l2loss_lambda
        self.kg_l2loss_lambda = args.kg_l2loss_lambda

        self.user_embed = nn.Embedding(self.n_users, self.embed_dim)
        self.item_embed = nn.Embedding(self.n_items, self.embed_dim)
        nn.init.xavier_uniform_(self.user_embed.weight)
        nn.init.xavier_uniform_(self.item_embed.weight)

        self.entity_embed = nn.Embedding(self.n_entities, self.embed_dim)
        self.relation_embed = nn.Embedding(self.n_relations, self.relation_dim)
        nn.init.xavier_uniform_(self.entity_embed.weight)
        nn.init.xavier_uniform_(self.relation_embed.weight)

        # TransR 
        self.trans_M = nn.Parameter(torch.Tensor(self.n_relations, self.embed_dim, self.relation_dim))
        nn.init.xavier_uniform_(self.trans_M)


    def calc_kg_loss_TransR(self, h, r, pos_t, neg_t):
        """
        h:      (kg_batch_size)
        r:      (kg_batch_size)
        pos_t:  (kg_batch_size)
        neg_t:  (kg_batch_size)
        """
        r_embed = self.relation_embed(r)                                                # (kg_batch_size, relation_dim)
        W_r = self.trans_M[r]                                                           # (kg_batch_size, embed_dim, relation_dim)

        h_embed = self.entity_embed(h)                                                  # (kg_batch_size, embed_dim)
        pos_t_embed = self.entity_embed(pos_t)                                          # (kg_batch_size, embed_dim)
        neg_t_embed = self.entity_embed(neg_t)                                          # (kg_batch_size, embed_dim)

        # 1. 计算头实体，尾实体和负采样的尾实体在对应关系空间中的投影嵌入
        r_mul_h = torch.bmm(h_embed.unsqueeze(1), W_r).squeeze(1)                                               # (kg_batch_size, relation_dim)
        r_mul_pos_t = torch.bmm(pos_t_embed.unsqueeze(1), W_r).squeeze(1)                                       # (kg_batch_size, relation_dim)
        r_mul_neg_t = torch.bmm(neg_t_embed.unsqueeze(1), W_r).squeeze(1)                                       # (kg_batch_size, relation_dim)

        # 2. 对关系嵌入，头实体嵌入，尾实体嵌入，负采样的尾实体嵌入进行L2范数归一化
        # 一个很小的数，用于避免除以0的情况
        # 使用clamp确保l2_norm不会小于epsilon
        epsilon = 1e-10  
        l2_norm = torch.clamp(torch.norm(r_embed, p=2), min=epsilon) 
        r_embed = r_embed / l2_norm

        l2_norm = torch.clamp(torch.norm(r_mul_h, p=2), min=epsilon) 
        r_mul_h = r_mul_h / l2_norm

        l2_norm = torch.clamp(torch.norm(r_mul_pos_t, p=2), min=epsilon) 
        r_mul_pos_t = r_mul_pos_t / l2_norm

        l2_norm = torch.clamp(torch.norm(r_mul_neg_t, p=2), min=epsilon) 
        r_mul_neg_t = r_mul_neg_t / l2_norm

        # 3. 分别计算正样本三元组 (h_embed, r_embed, pos_t_embed) 和负样本三元组 (h_embed, r_embed, neg_t_embed) 的得分
        pos_score = (r_mul_h + r_embed - r_mul_pos_t).norm(2).pow(2)                                                                   # (kg_batch_size)
        neg_score = (r_mul_h + r_embed - r_mul_neg_t).norm(2).pow(2)                                                                   # (kg_batch_size)

        # 4. 使用 BPR Loss 进行优化，尽可能使负样本的得分大于正样本的得分
        # 1e-9 防止 NAN
        kg_loss = (-1.0) * torch.log(1e-9 + F.sigmoid(neg_score - pos_score))
        kg_loss = kg_loss.mean()

        l2_loss = _L2_loss_mean(r_mul_h) + _L2_loss_mean(r_embed) + _L2_loss_mean(r_mul_pos_t) + _L2_loss_mean(r_mul_neg_t)
        loss = kg_loss + self.kg_l2loss_lambda * l2_loss
        return loss


    def calc_kg_loss_TransE(self, h, r, pos_t, neg_t):
        """
        h:      (kg_batch_size)
        r:      (kg_batch_size)
        pos_t:  (kg_batch_size)
        neg_t:  (kg_batch_size)
        """
        r_embed = self.relation_embed(r)                                                # (kg_batch_size, relation_dim)
        
        h_embed = self.entity_embed(h)                                                  # (kg_batch_size, embed_dim)
        pos_t_embed = self.entity_embed(pos_t)                                          # (kg_batch_size, embed_dim)
        neg_t_embed = self.entity_embed(neg_t)                                          # (kg_batch_size, embed_dim)

        # 5. 对关系嵌入，头实体嵌入，尾实体嵌入，负采样的尾实体嵌入进行L2范数归一化
        epsilon = 1e-10  
        l2_norm = torch.clamp(torch.norm(r_embed, p=2), min=epsilon) 
        r_embed = r_embed / l2_norm

        l2_norm = torch.clamp(torch.norm(h_embed, p=2), min=epsilon) 
        h_embed = h_embed / l2_norm

        l2_norm = torch.clamp(torch.norm(pos_t_embed, p=2), min=epsilon) 
        pos_t_embed = pos_t_embed / l2_norm

        l2_norm = torch.clamp(torch.norm(neg_t_embed, p=2), min=epsilon) 
        neg_t_embed = neg_t_embed / l2_norm

        # 6. 分别计算正样本三元组 (h_embed, r_embed, pos_t_embed) 和负样本三元组 (h_embed, r_embed, neg_t_embed) 的得分
        pos_score =  torch.abs(h_embed + r_embed - pos_t_embed)                                                                    # (kg_batch_size)
        neg_score =  torch.abs(h_embed + r_embed - neg_t_embed)                                                                    # (kg_batch_size)

        # 7. 使用 BPR Loss 进行优化，尽可能使负样本的得分大于正样本的得分
        # 1e-9 防止 NAN
        kg_loss = (-1.0) * torch.log(1e-9 + F.sigmoid(neg_score - pos_score))
        kg_loss = kg_loss.mean()

        l2_loss = _L2_loss_mean(h_embed) + _L2_loss_mean(r_embed) + _L2_loss_mean(pos_t_embed) + _L2_loss_mean(neg_t_embed)
        loss = kg_loss + self.kg_l2loss_lambda * l2_loss
        return loss


    def calc_cf_loss(self, user_ids, item_pos_ids, item_neg_ids):
        """
        user_ids:       (cf_batch_size)
        item_pos_ids:   (cf_batch_size)
        item_neg_ids:   (cf_batch_size)
        """
        user_embed = self.user_embed(user_ids)                                          # (cf_batch_size, embed_dim)
        item_pos_embed = self.item_embed(item_pos_ids)                                  # (cf_batch_size, embed_dim)
        item_neg_embed = self.item_embed(item_neg_ids)                                  # (cf_batch_size, embed_dim)

        item_pos_kg_embed = self.entity_embed(item_pos_ids)                             # (cf_batch_size, embed_dim)
        item_neg_kg_embed = self.entity_embed(item_neg_ids)                             # (cf_batch_size, embed_dim)
        
        # 8. 为 物品嵌入 注入 实体嵌入的语义信息
        # 逐元素相加
        if self.inject_manner == 1:
            item_pos_cf_embed = item_pos_embed + item_pos_kg_embed                                                            # (cf_batch_size, embed_dim)
            item_neg_cf_embed = item_neg_embed + item_neg_kg_embed                                                            # (cf_batch_size, embed_dim)
        # multi
        elif self.inject_manner == 2:
            item_pos_cf_embed = item_pos_embed * item_pos_kg_embed                                                            # (cf_batch_size, embed_dim)
            item_neg_cf_embed = item_neg_embed * item_neg_kg_embed                                                            # (cf_batch_size, embed_dim)  
        # concat 
        else:
            item_pos_intergrated = torch.cat([item_pos_embed, item_pos_kg_embed], dim=1)
            item_neg_intergrated = torch.cat([item_neg_embed, item_neg_kg_embed], dim=1)
            item_pos_cf_embed = self.trans(item_pos_intergrated)
            item_neg_cf_embed = self.trans(item_neg_intergrated)

        pos_score = torch.sum(user_embed * item_pos_cf_embed, dim=1)                    # (cf_batch_size)
        neg_score = torch.sum(user_embed * item_neg_cf_embed, dim=1)                    # (cf_batch_size)

        cf_loss = (-1.0) * torch.log(1e-10 + F.sigmoid(pos_score - neg_score))
        cf_loss = torch.mean(cf_loss)

        l2_loss = _L2_loss_mean(user_embed) + _L2_loss_mean(item_pos_cf_embed) + _L2_loss_mean(item_neg_cf_embed)
        loss = cf_loss + self.cf_l2loss_lambda * l2_loss
        return loss


    def calc_loss(self, user_ids, item_pos_ids, item_neg_ids, h, r, pos_t, neg_t):
        """
        user_ids:       (cf_batch_size)
        item_pos_ids:   (cf_batch_size)
        item_neg_ids:   (cf_batch_size)

        h:              (kg_batch_size)
        r:              (kg_batch_size)
        pos_t:          (kg_batch_size)
        neg_t:          (kg_batch_size)
        """
        if self.KG_embedding_type == 'TransR':
            calc_kg_loss = self.calc_kg_loss_TransR
        elif self.KG_embedding_type == 'TransE':
            calc_kg_loss = self.calc_kg_loss_TransE
        
        kg_loss = calc_kg_loss(h, r, pos_t, neg_t)
        cf_loss = self.calc_cf_loss(user_ids, item_pos_ids, item_neg_ids)
        
        loss = kg_loss + cf_loss
        return loss


    def calc_score(self, user_ids, item_ids):
        """
        user_ids:  (n_users)
        item_ids:  (n_items)
        """
        user_embed = self.user_embed(user_ids)                                          # (n_users, embed_dim)

        item_embed = self.item_embed(item_ids)                                          # (n_items, embed_dim)
        item_kg_embed = self.entity_embed(item_ids)                                     # (n_items, embed_dim)

        # 9. 为 物品嵌入 注入 实体嵌入的语义信息
        # 逐元素相加
        if self.inject_manner == 1:
            item_cf_embed = item_embed + item_kg_embed                                      # (n_items, embed_dim)
        # multi
        elif self.inject_manner == 2:
            item_cf_embed = item_embed * item_kg_embed                                      # (n_items, embed_dim)
        # concat
        else:
            item_emb_intergrated = torch.cat([item_embed, item_kg_embed], dim = 1)
            item_cf_embed = self.trans(item_emb_intergrated)

        cf_score = torch.matmul(user_embed, item_cf_embed.transpose(0, 1))              # (n_users, n_items)
        
        return cf_score


    def forward(self, *input, is_train):
        if is_train:
            return self.calc_loss(*input)
        else:
            return self.calc_score(*input)


