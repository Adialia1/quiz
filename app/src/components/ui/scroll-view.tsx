import React from 'react';
import { ScrollView as RNScrollView } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledScrollView = styled(
  RNScrollView,
  {},
  {
    componentName: 'ScrollView',
  }
);

export const ScrollView = StyledScrollView;
