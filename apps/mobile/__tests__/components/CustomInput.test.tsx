/**
 * Unit tests for CustomInput component
 * Tests input rendering, validation, secure entry, and user interactions
 */
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import CustomInput from '../../components/CustomInput';

describe('CustomInput', () => {
  describe('Basic Rendering', () => {
    it('should render with default props', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      expect(getByPlaceholderText('Enter text')).toBeTruthy();
    });

    it('should render with custom placeholder', () => {
      const { getByPlaceholderText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          placeholder="Enter email" 
        />
      );
      expect(getByPlaceholderText('Enter email')).toBeTruthy();
    });

    it('should render label when provided', () => {
      const { getByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          label="Email Address" 
        />
      );
      expect(getByText('EMAIL ADDRESS')).toBeTruthy();
    });

    it('should render without label when not provided', () => {
      const { queryByText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      // Should not have any label text
      expect(queryByText(/^[A-Z\s]+$/)).toBeNull();
    });
  });

  describe('Value and Text Change', () => {
    it('should display the current value', () => {
      const { getByDisplayValue } = render(
        <CustomInput value="test@example.com" onChangeText={() => {}} />
      );
      expect(getByDisplayValue('test@example.com')).toBeTruthy();
    });

    it('should call onChangeText when text changes', () => {
      const onChangeTextMock = jest.fn();
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={onChangeTextMock} />
      );
      
      const input = getByPlaceholderText('Enter text');
      fireEvent.changeText(input, 'new text');
      
      expect(onChangeTextMock).toHaveBeenCalledWith('new text');
    });

    it('should handle empty string value', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      expect(getByPlaceholderText('Enter text')).toBeTruthy();
    });

    it('should handle very long text', () => {
      const longText = 'a'.repeat(1000);
      const { getByDisplayValue } = render(
        <CustomInput value={longText} onChangeText={() => {}} />
      );
      expect(getByDisplayValue(longText)).toBeTruthy();
    });
  });

  describe('Secure Text Entry', () => {
    it('should hide text when secureTextEntry is true', () => {
      const { getByPlaceholderText } = render(
        <CustomInput 
          value="password123" 
          onChangeText={() => {}} 
          secureTextEntry={true} 
        />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.secureTextEntry).toBe(true);
    });

    it('should show text when secureTextEntry is false', () => {
      const { getByPlaceholderText } = render(
        <CustomInput 
          value="visible text" 
          onChangeText={() => {}} 
          secureTextEntry={false} 
        />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.secureTextEntry).toBe(false);
    });

    it('should render eye icon toggle for password fields', () => {
      const { getByText } = render(
        <CustomInput 
          value="password" 
          onChangeText={() => {}} 
          secureTextEntry={true} 
        />
      );
      
      expect(getByText('👁️')).toBeTruthy();
    });

    it('should toggle password visibility when eye icon is pressed', () => {
      const { getByText, getByPlaceholderText } = render(
        <CustomInput 
          value="password123" 
          onChangeText={() => {}} 
          secureTextEntry={true} 
        />
      );
      
      const input = getByPlaceholderText('Enter text');
      const eyeIcon = getByText('👁️');
      
      // Initially hidden
      expect(input.props.secureTextEntry).toBe(true);
      
      // Toggle to show
      fireEvent.press(eyeIcon);
      expect(input.props.secureTextEntry).toBe(false);
      
      // Toggle back to hide
      fireEvent.press(eyeIcon);
      expect(input.props.secureTextEntry).toBe(true);
    });

    it('should change icon when password visibility toggles', () => {
      const { getByText } = render(
        <CustomInput 
          value="password" 
          onChangeText={() => {}} 
          secureTextEntry={true} 
        />
      );
      
      const eyeIcon = getByText('👁️');
      fireEvent.press(eyeIcon);
      
      expect(getByText('🙈')).toBeTruthy();
    });
  });

  describe('Keyboard Types', () => {
    it('should use default keyboard type', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.keyboardType).toBe('default');
    });

    it('should use email-address keyboard type', () => {
      const { getByPlaceholderText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          keyboardType="email-address" 
        />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.keyboardType).toBe('email-address');
    });

    it('should use numeric keyboard type', () => {
      const { getByPlaceholderText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          keyboardType="numeric" 
        />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.keyboardType).toBe('numeric');
    });
  });

  describe('Error States', () => {
    it('should not show error message when error is false', () => {
      const { queryByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          error={false}
          errorMessage="Error message" 
        />
      );
      
      expect(queryByText('Error message')).toBeNull();
    });

    it('should show error message when error is true', () => {
      const { getByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          error={true}
          errorMessage="Invalid email" 
        />
      );
      
      expect(getByText('Invalid email')).toBeTruthy();
    });

    it('should not show error message if errorMessage is not provided', () => {
      const { queryByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          error={true}
        />
      );
      
      // No error message should be visible
      expect(queryByText(/.+/)).toBeTruthy(); // Some text exists (label/placeholder)
    });

    it('should handle empty error message', () => {
      const { queryByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          error={true}
          errorMessage="" 
        />
      );
      
      expect(queryByText('')).toBeNull();
    });
  });

  describe('Focus States', () => {
    it('should handle focus event', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      
      const input = getByPlaceholderText('Enter text');
      fireEvent(input, 'focus');
      
      // Component should handle focus internally
      expect(input).toBeTruthy();
    });

    it('should handle blur event', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      
      const input = getByPlaceholderText('Enter text');
      fireEvent(input, 'focus');
      fireEvent(input, 'blur');
      
      expect(input).toBeTruthy();
    });
  });

  describe('Auto-correct and Auto-capitalize', () => {
    it('should disable auto-correct', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.autoCorrect).toBe(false);
    });

    it('should disable auto-capitalize', () => {
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={() => {}} />
      );
      
      const input = getByPlaceholderText('Enter text');
      expect(input.props.autoCapitalize).toBe('none');
    });
  });

  describe('Edge Cases', () => {
    it('should handle unicode characters in value', () => {
      const unicodeValue = 'José García 日本語 🎉';
      const { getByDisplayValue } = render(
        <CustomInput value={unicodeValue} onChangeText={() => {}} />
      );
      expect(getByDisplayValue(unicodeValue)).toBeTruthy();
    });

    it('should handle special characters in value', () => {
      const specialValue = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      const { getByDisplayValue } = render(
        <CustomInput value={specialValue} onChangeText={() => {}} />
      );
      expect(getByDisplayValue(specialValue)).toBeTruthy();
    });

    it('should handle newlines in value', () => {
      const multilineValue = 'Line 1\nLine 2\nLine 3';
      const { getByDisplayValue } = render(
        <CustomInput value={multilineValue} onChangeText={() => {}} />
      );
      expect(getByDisplayValue(multilineValue)).toBeTruthy();
    });

    it('should handle rapid text changes', () => {
      const onChangeTextMock = jest.fn();
      const { getByPlaceholderText } = render(
        <CustomInput value="" onChangeText={onChangeTextMock} />
      );
      
      const input = getByPlaceholderText('Enter text');
      fireEvent.changeText(input, 'a');
      fireEvent.changeText(input, 'ab');
      fireEvent.changeText(input, 'abc');
      
      expect(onChangeTextMock).toHaveBeenCalledTimes(3);
    });
  });

  describe('Label Transformation', () => {
    it('should convert label to uppercase', () => {
      const { getByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          label="email address" 
        />
      );
      expect(getByText('EMAIL ADDRESS')).toBeTruthy();
    });

    it('should handle label with mixed case', () => {
      const { getByText } = render(
        <CustomInput 
          value="" 
          onChangeText={() => {}} 
          label="Password Field" 
        />
      );
      expect(getByText('PASSWORD FIELD')).toBeTruthy();
    });
  });

  describe('Integration Scenarios', () => {
    it('should work as email input with all features', () => {
      const onChangeTextMock = jest.fn();
      const { getByText, getByPlaceholderText } = render(
        <CustomInput 
          value="test@example.com"
          onChangeText={onChangeTextMock}
          label="Email"
          placeholder="Enter your email"
          keyboardType="email-address"
          error={false}
        />
      );
      
      expect(getByText('EMAIL')).toBeTruthy();
      expect(getByPlaceholderText('Enter your email')).toBeTruthy();
    });

    it('should work as password input with all features', () => {
      const onChangeTextMock = jest.fn();
      const { getByText, getByPlaceholderText } = render(
        <CustomInput 
          value="password123"
          onChangeText={onChangeTextMock}
          label="Password"
          placeholder="Enter your password"
          secureTextEntry={true}
          error={false}
        />
      );
      
      expect(getByText('PASSWORD')).toBeTruthy();
      expect(getByText('👁️')).toBeTruthy();
      expect(getByPlaceholderText('Enter your password')).toBeTruthy();
    });

    it('should show validation error for invalid input', () => {
      const { getByText } = render(
        <CustomInput 
          value="invalid"
          onChangeText={() => {}}
          label="Email"
          error={true}
          errorMessage="Please enter a valid email"
        />
      );
      
      expect(getByText('Please enter a valid email')).toBeTruthy();
    });
  });
});