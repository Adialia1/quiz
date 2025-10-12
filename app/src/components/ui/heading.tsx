import React from 'react';
import { Text } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledHeading = styled(
  Text,
  {
    color: '$textPrimary',
    fontFamily: '$heading',
    fontWeight: '$bold',
  },
  {
    componentName: 'Heading',
    ancestorStyle: ['_heading'],
  }
);

export const Heading = StyledHeading;
