import React from 'react';
import { View } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledHStack = styled(
  View,
  {
    flexDirection: 'row',
  },
  {
    componentName: 'HStack',
  }
);

export const HStack = StyledHStack;
