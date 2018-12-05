<template>
  <div
    v-if="isOpened"
    class="drop-down-options empty-options"
    v-on-clickaway="closeDropDown">
    <div v-if="dropDownOptions.length == 0">
      <div class="option" style="padding-left: 16px;">
        <span>{{ noOptionsMessage }}</span>
      </div>
    </div>
    <div v-if="dropDownOptions.length > 0">
      <div v-for="(option, i) in dropDownOptions" :key="option.id">
        <div
          @click="filterValueSelected(option, i)"
          :class="[isSelected(option, i) ? 'selected' : '', 'option']">
          <svg-icon
            :class="[isSelected(option, i) ? '' : 'hidden-checkmark']"
            icon-name="check"><icon-check />
          </svg-icon>
          <p>{{ option.label }}</p>
        </div>
      </div>
      <div @click="resetSelections()" class="option reset">
          <svg-icon
            icon-name="cross"><icon-cross />
          </svg-icon>
        <p>Tyhjennä valinnat</p>
      </div>
    </div>
  </div>
</template>

<script>
import { findValueFromDropDownOptions } from '../../utils/dropDownHelper.js';

import SvgIcon from '../icons/SvgIcon';
import IconCheck from '../icons/IconCheck';
import IconCross from '../icons/IconCross';
import { directive as onClickaway } from 'vue-clickaway';

export default {
  components: {
    SvgIcon,
    IconCheck,
    IconCross
  },
  directives: {
    onClickaway: onClickaway
  },
  props: {
    selectedIndexes: Array,
    isOpened: Boolean,
    dropDownOptions: Array,
    selectedOptionsMapper: Object,
    noOptionsMessage: String
  },
  methods: {
    filterValueSelected(option, index) {
      this.handleDropDownSelectedIndicator(index);

      // TODO: ensure that this filters multiple tags in filterValueHelper.js
      if (option && option.value !== '') {
        // do filtering by filter key
        const selectedValue = findValueFromDropDownOptions(option.value, this.dropDownOptions);
        this.applyFilter(selectedValue);
      }
    },
    isSelected(option, index) {
      if (this.selectedIndexes && this.selectedIndexes.length > 0) {
        if (this.selectedIndexes.indexOf(index) == -1) {
          return false;
        } else {
          return true;
        }
      }
    },
    applyFilter(selectedFilter = null) {
      this.$emit('applyFilter', selectedFilter);
    },
    handleDropDownSelectedIndicator(index) {
      // update dropdownlist selected value indicator as selected
      this.$emit('addToSelectedIndexes', index);
    },
    resetSelections() {
      this.$emit('resetTags');
      this.applyFilter();
    },
    closeDropDown() {
      this.$emit('closeDropDown');
    }
  }
};
</script>

<style scoped>
.drop-down-options {
  position: absolute;
  top: 44px;
  left: 0;
  background-color: #ffffff;
  min-width: 200px;
  z-index: 2;
  text-align: left;
  border: 1px solid #e1e1e1;
  border-radius: 2px;
  -webkit-box-shadow: 6px 8px 17px -6px rgba(80, 80, 80, 0.35);
  -moz-box-shadow: 6px 8px 17px -6px rgba(80, 80, 80, 0.35);
  box-shadow: 6px 8px 17px -6px rgba(80, 80, 80, 0.35);
}

.option {
  padding: 8px 6px 7px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
  font-weight: 500;
  color: #555555;
  vertical-align: middle;
}

.option:hover {
  background-color: #f3fbfa;
  color: #111111;
  cursor: pointer;
  cursor: hand;
}

.option p {
  display: inline-block;
  margin: 0;
  text-transform: lowercase;
}

.option p::first-letter {
  text-transform: uppercase;
}

.option svg {
  height: 10px;
  margin-right: 5px;
  vertical-align: middle;
}

.selected {
  font-weight: 600;
  color: #111111;
}

.reset {
  color: #aaaaaa;
}

.reset:hover {
  color: #888888;
}

.hidden-checkmark {
  opacity: 0;
}

.empty-options {
  min-width: 250px;
}

@media (max-width: 700px) {
  .option {
    padding: 12px 6px 11px;
  }
}
</style>