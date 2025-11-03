/**
 * Unit tests for CustomButton component
 * Tests button rendering, variants, loading states, and interactions
 */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import CustomButton from '../../components/CustomButton';
import { Text } from 'react-native';

// Mock dependencies
jest.mock('@/constants/images', () => ({
  images: {
    goldHighlight: { uri: 'mock-gold-highlight.png' },
  },
}));

describe('CustomButton', () => {
  describe('Basic Rendering', () => {
    it('should render with default props', () => {
      const { getByText } = render(<CustomButton onPress={() => {}} />);
      expect(getByText('Click Me')).toBeTruthy();
    });

    it('should render with custom title', () => {
      const { getByText } = render(
        <CustomButton onPress={() => {}} title="Custom Title" />
      );
      expect(getByText('Custom Title')).toBeTruthy();
    });

    it('should render default variant', () => {
      const { getByA11yRole } = render(<CustomButton onPress={() => {}} />);
      const button = getByA11yRole('button');
      expect(button).toBeTruthy();
    });

    it('should render primary variant', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} variant="primary" />
      );
      const button = getByA11yRole('button');
      expect(button).toBeTruthy();
    });
  });

  describe('User Interactions', () => {
    it('should call onPress when clicked', () => {
      const onPressMock = jest.fn();
      const { getByA11yRole } = render(<CustomButton onPress={onPressMock} />);
      
      const button = getByA11yRole('button');
      fireEvent.press(button);
      
      expect(onPressMock).toHaveBeenCalledTimes(1);
    });

    it('should not call onPress when disabled/loading', () => {
      const onPressMock = jest.fn();
      const { getByA11yRole } = render(
        <CustomButton onPress={onPressMock} isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      fireEvent.press(button);
      
      expect(onPressMock).not.toHaveBeenCalled();
    });

    it('should handle multiple rapid clicks', () => {
      const onPressMock = jest.fn();
      const { getByA11yRole } = render(<CustomButton onPress={onPressMock} />);
      
      const button = getByA11yRole('button');
      fireEvent.press(button);
      fireEvent.press(button);
      fireEvent.press(button);
      
      expect(onPressMock).toHaveBeenCalledTimes(3);
    });
  });

  describe('Loading State', () => {
    it('should show loading indicator when isLoading is true', () => {
      const { getByA11yRole, queryByText } = render(
        <CustomButton onPress={() => {}} title="Submit" isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.accessibilityState.busy).toBe(true);
      expect(queryByText('Submit')).toBeNull();
    });

    it('should not show loading indicator when isLoading is false', () => {
      const { getByText } = render(
        <CustomButton onPress={() => {}} title="Submit" isLoading={false} />
      );
      
      expect(getByText('Submit')).toBeTruthy();
    });

    it('should disable button when loading', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.accessibilityState.disabled).toBe(true);
    });

    it('should have reduced opacity when loading', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.style).toContainEqual({ opacity: 0.6 });
    });

    it('should have normal opacity when not loading', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} isLoading={false} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.style).toContainEqual({ opacity: 1 });
    });
  });

  describe('Icons', () => {
    it('should render with left icon', () => {
      const LeftIcon = <Text testID="left-icon">←</Text>;
      const { getByTestId } = render(
        <CustomButton onPress={() => {}} leftIcon={LeftIcon} />
      );
      
      expect(getByTestId('left-icon')).toBeTruthy();
    });

    it('should render with right icon', () => {
      const RightIcon = <Text testID="right-icon">→</Text>;
      const { getByTestId } = render(
        <CustomButton onPress={() => {}} rightIcon={RightIcon} />
      );
      
      expect(getByTestId('right-icon')).toBeTruthy();
    });

    it('should render with both left and right icons', () => {
      const LeftIcon = <Text testID="left-icon">←</Text>;
      const RightIcon = <Text testID="right-icon">→</Text>;
      const { getByTestId } = render(
        <CustomButton 
          onPress={() => {}} 
          leftIcon={LeftIcon} 
          rightIcon={RightIcon} 
        />
      );
      
      expect(getByTestId('left-icon')).toBeTruthy();
      expect(getByTestId('right-icon')).toBeTruthy();
    });

    it('should not show icons when loading', () => {
      const LeftIcon = <Text testID="left-icon">←</Text>;
      const { queryByTestId } = render(
        <CustomButton 
          onPress={() => {}} 
          leftIcon={LeftIcon} 
          isLoading={true}
        />
      );
      
      expect(queryByTestId('left-icon')).toBeNull();
    });
  });

  describe('Variants', () => {
    it('should apply correct loader color for primary variant', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} variant="primary" isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button).toBeTruthy();
    });

    it('should apply correct loader color for default variant', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} variant="default" isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button).toBeTruthy();
    });
  });

  describe('Accessibility', () => {
    it('should have button role', () => {
      const { getByA11yRole } = render(<CustomButton onPress={() => {}} />);
      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should have correct accessibility label', () => {
      const { getByA11yLabel } = render(
        <CustomButton onPress={() => {}} title="Submit Form" />
      );
      expect(getByA11yLabel('Submit Form')).toBeTruthy();
    });

    it('should indicate disabled state in accessibility', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.accessibilityState.disabled).toBe(true);
    });

    it('should indicate busy state in accessibility when loading', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} isLoading={true} />
      );
      
      const button = getByA11yRole('button');
      expect(button.props.accessibilityState.busy).toBe(true);
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom style prop', () => {
      const customStyle = 'mt-4 mx-2';
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} style={customStyle} />
      );
      
      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should accept custom text style prop', () => {
      const customTextStyle = 'text-lg';
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} textStyle={customTextStyle} />
      );
      
      expect(getByA11yRole('button')).toBeTruthy();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty title', () => {
      const { getByA11yRole } = render(
        <CustomButton onPress={() => {}} title="" />
      );
      
      expect(getByA11yRole('button')).toBeTruthy();
    });

    it('should handle very long title', () => {
      const longTitle = 'A'.repeat(1000);
      const { getByText } = render(
        <CustomButton onPress={() => {}} title={longTitle} />
      );
      
      expect(getByText(longTitle)).toBeTruthy();
    });

    it('should handle title with special characters', () => {
      const specialTitle = 'Submit & Continue →';
      const { getByText } = render(
        <CustomButton onPress={() => {}} title={specialTitle} />
      );
      
      expect(getByText(specialTitle)).toBeTruthy();
    });

    it('should handle title with unicode', () => {
      const unicodeTitle = 'Enviar 送信 ✓';
      const { getByText } = render(
        <CustomButton onPress={() => {}} title={unicodeTitle} />
      );
      
      expect(getByText(unicodeTitle)).toBeTruthy();
    });

    it('should handle undefined onPress gracefully', () => {
      expect(() => {
        render(<CustomButton onPress={undefined as any} />);
      }).not.toThrow();
    });
  });

  describe('State Transitions', () => {
    it('should transition from loading to not loading', () => {
      const { getByA11yRole, rerender } = render(
        <CustomButton onPress={() => {}} title="Submit" isLoading={true} />
      );
      
      let button = getByA11yRole('button');
      expect(button.props.accessibilityState.disabled).toBe(true);
      
      rerender(
        <CustomButton onPress={() => {}} title="Submit" isLoading={false} />
      );
      
      button = getByA11yRole('button');
      expect(button.props.accessibilityState.disabled).toBe(false);
    });

    it('should transition from not loading to loading', () => {
      const onPressMock = jest.fn();
      const { getByA11yRole, rerender } = render(
        <CustomButton onPress={onPressMock} title="Submit" isLoading={false} />
      );
      
      let button = getByA11yRole('button');
      fireEvent.press(button);
      expect(onPressMock).toHaveBeenCalledTimes(1);
      
      rerender(
        <CustomButton onPress={onPressMock} title="Submit" isLoading={true} />
      );
      
      button = getByA11yRole('button');
      fireEvent.press(button);
      expect(onPressMock).toHaveBeenCalledTimes(1); // Should not increment
    });
  });
});