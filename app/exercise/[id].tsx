import { useLocalSearchParams } from 'expo-router';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

const Details = () => {
    //extratct route param on expo
    const { id } = useLocalSearchParams();
    return (
        <View>
            <Text>Movie details: {id}</Text>
        </View>
    )
}

export default Details

const styles = StyleSheet.create({})