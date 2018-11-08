import Vue from 'vue';
import { mapGetters, mapActions } from 'vuex';
import api from '../../../api';
import {
  namespace,
  storeStateNames,
  eventGetters,
  eventMutations,
  eventActions
} from './eventConsts';

export const mapEventGetters = getters => mapGetters(namespace, getters);
export const mapEventActions = actions => mapActions(namespace, actions);

export default {
  namespaced: true,
  state: {
    [storeStateNames.ITEMS]: []
  },
  getters: {
    [eventGetters.GET_EVENTS]: state => state[storeStateNames.ITEMS]
  },
  mutations: {
    [eventMutations.SET_EVENTS](state, events) {
      Vue.set(state, storeStateNames.ITEMS, events);
    }
  },
  actions: {
    async [eventActions.ADD_NEW_EVENT]({ dispatch }, params) {
      await api.events.addNewComment(params.event);
      dispatch(eventActions.GET_EVENTS_BY_SUGGESTION_ID, params.suggestionId);
    },
    async [eventActions.GET_EVENTS_BY_SUGGESTION_ID]({ commit }, suggestionId) {
      const result = await api.events.getEventsBySuggestionId(suggestionId);
      commit(eventMutations.SET_EVENTS, result.data);
    }
  }
};