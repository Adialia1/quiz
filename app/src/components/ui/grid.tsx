import React from 'react';
import { View, ViewProps } from 'react-native';
import { styled } from '@gluestack-style/react';

const StyledGrid = styled(
  View,
  {
    width: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  {
    componentName: 'Grid',
  }
);

const StyledGridItem = styled(
  View,
  {
    width: '100%',
  },
  {
    componentName: 'GridItem',
  }
);

export const Grid = StyledGrid;
export const GridItem = StyledGridItem;
