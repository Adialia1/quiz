import React from 'react';
import { Pressable as RNPressable } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledPressable = styled(
  RNPressable,
  {},
  {
    componentName: 'Pressable',
  }
);

export const Pressable = StyledPressable;
