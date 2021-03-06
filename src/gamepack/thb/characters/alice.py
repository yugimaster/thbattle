# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DrawCards, DropCardStage, DropCards, PlayerDeath
from gamepack.thb.actions import PostCardMigrationHandler, UserAction, random_choose_card
from gamepack.thb.actions import user_choose_players
from gamepack.thb.cards import Skill, t_None
from gamepack.thb.characters.baseclasses import Character, register_character_to
from gamepack.thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class LittleLegion(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class LittleLegionDrawCards(DrawCards):
    pass


class LittleLegionAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        if not card:
            card = random_choose_card(cats)
            if not card:
                return False

        self.card = card
        g.players.exclude(tgt).reveal(card)
        g.process_action(
            DropCards(src, tgt, cards=[card])
        )
        return True


class LittleLegionDrawHandler(EventHandler):
    interested = ('choose_target',)

    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            lca, tl = arg
            if 'equipment' not in lca.card.category: return arg

            src = lca.source
            if src.dead or not src.has_skill(LittleLegion): return arg
            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return arg
            g = Game.getgame()
            g.process_action(LittleLegionDrawCards(src, 1))

        return arg


class LittleLegionDropHandler(EventHandler):
    interested = ('post_card_migration',)
    group = PostCardMigrationHandler

    def handle(self, p, arg):
        if not p.has_skill(LittleLegion):
            return True

        equips = p.equips
        if not any(_from is equips for _, _from, _, _ in arg.get_movements()):
            return True

        g = Game.getgame()
        self.source = p
        if not user_input([p], ChooseOptionInputlet(self, (False, True))):
            return True

        tl = user_choose_players(self, p, g.players.exclude(p))
        if tl:
            assert len(tl) == 1
            g.process_action(LittleLegionAction(p, tl[0]))

        return True

    def cond(self, cl):
        return True

    def choose_player_target(self, tl):
        if not tl:
            return tl, False

        tgt = tl[0]
        if tgt is self.source:
            return [], False

        return ([tgt], bool(tgt.equips or tgt.cards or tgt.showncards))


class MaidensBunraku(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MaidensBunrakuKOF(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MaidensBunrakuHandler(EventHandler):
    interested = ('action_apply', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, DropCardStage):
            tgt = act.target
            if not tgt.has_skill(MaidensBunraku) and not tgt.has_skill(MaidensBunrakuKOF): return act
            act.dropn -= self.calc_x(tgt)

        return act

    @staticmethod
    def calc_x(p):
        amount = (len(p.equips) + 1) / 2
        return max(amount, 1)


class MaidensBunrakuKOFAction(UserAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt, n = self.target, self.amount
        return Game.getgame().process_action(Damage(None, tgt, n))


class MaidensBunrakuKOFHandler(EventHandler):
    interested = ('action_apply', )
    execute_after = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            tgt = act.target
            if not tgt.has_skill(MaidensBunrakuKOF): return act
            g = Game.getgame()
            op = g.get_opponent(tgt)
            amount = MaidensBunrakuHandler.calc_x(tgt)
            g.process_action(MaidensBunrakuKOFAction(tgt, op, amount))

        return act


@register_character_to('common', '-kof')
class Alice(Character):
    skills = [LittleLegion, MaidensBunraku]
    eventhandlers_required = [
        LittleLegionDrawHandler,
        LittleLegionDropHandler,
        MaidensBunrakuHandler,
    ]
    maxlife = 3


@register_character_to('kof')
class AliceKOF(Character):
    skills = [LittleLegion, MaidensBunrakuKOF]
    eventhandlers_required = [
        LittleLegionDrawHandler,
        LittleLegionDropHandler,
        MaidensBunrakuHandler,
        MaidensBunrakuKOFHandler,
    ]
    maxlife = 3
