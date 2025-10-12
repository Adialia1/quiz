import React from 'react';
import { View } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledBox = styled(
  View,
  {
    flex: 1,
    flexDirection: 'column',
    position: 'relative',
    zIndex: 0,
    borderWidth: 0,
    minWidth: 0,
    minHeight: 0,
    backgroundColor: 'transparent',
  },
  {
    componentName: 'Box',
  }
);

export const Box = StyledBox;
