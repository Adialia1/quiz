import React from 'react';
import { View } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledVStack = styled(
  View,
  {
    flexDirection: 'column',
  },
  {
    componentName: 'VStack',
  }
);

export const VStack = StyledVStack;
