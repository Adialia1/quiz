import React from 'react';
import { Text as RNText } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledText = styled(
  RNText,
  {
    color: '$textPrimary',
    fontFamily: '$body',
  },
  {
    componentName: 'Text',
    ancestorStyle: ['_text'],
  }
);

export const Text = StyledText;
