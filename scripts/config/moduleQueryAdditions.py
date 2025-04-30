# Define query additions for specific modules as a MuseumPlus search query
moduleQueryAdditions = {
    'Exhibition': '''
        <search>
            <expert>
                <and>
                    <notEqualsVocNodeExcludingHierarchy fieldPath="ExhTypeVoc" operand="240964"/>
                    <notEqualsVocNodeExcludingHierarchy fieldPath="ExhStatusVoc" operand="151965"/>
                    <notEqualsVocNodeExcludingHierarchy fieldPath="ExhStatusVoc" operand="25578"/>
                    <notEqualsVocNodeExcludingHierarchy fieldPath="ExhStatusVoc" operand="177046"/>
                    <notEqualsVocNodeExcludingHierarchy fieldPath="ExhStatusVoc" operand="148975"/>
                </and>
            </expert>
        </search>
        ''',
    'Multimedia': '''
        <search>
            <expert>
                <or>
                    <equalsVocNodeExcludingHierarchy fieldPath="MulUsageVoc" operand="20501"/>
                    <equalsVocNodeExcludingHierarchy fieldPath="MulUsageVoc" operand="205074"/>
                    <equalsVocNodeExcludingHierarchy fieldPath="MulUsageVoc" operand="237966"/>
                    <equalsVocNodeExcludingHierarchy fieldPath="MulUsageVoc" operand="237965"/>
                </or>
            </expert>
        </search>
        ''',
    'Object': '''
        <search>
            <expert>
                <equalsVocNodeExcludingHierarchy fieldPath="ObjInternetVoc" operand="20436"/>
            </expert>
        </search>
        ''',
    'ObjectGroup': '''
        <search>
            <expert>
                <endsWithTerm fieldPath="OgrNameTxt" operand="_public"/>
            </expert>
        </search>
    ''',
    'Registrar': '''
        <search>
            <expert>
                <and>
                    <or>
                        <equalsVocNodeExcludingHierarchy fieldPath="RegDecisionVoc" operand="140176"/>
                        <equalsVocNodeExcludingHierarchy fieldPath="RegDecisionVoc" operand="199969"/>
                    </or>
                    <and>
                        <notEqualsVocNodeExcludingHierarchy fieldPath="RegExhibitionRef.ExhTypeVoc" operand="240964"/>
                        <notEqualsVocNodeExcludingHierarchy fieldPath="RegExhibitionRef.ExhStatusVoc" operand="151965"/>
                        <notEqualsVocNodeExcludingHierarchy fieldPath="RegExhibitionRef.ExhStatusVoc" operand="25578"/>
                        <notEqualsVocNodeExcludingHierarchy fieldPath="RegExhibitionRef.ExhStatusVoc" operand="177046"/>
                        <notEqualsVocNodeExcludingHierarchy fieldPath="RegExhibitionRef.ExhStatusVoc" operand="148975"/>
                    </and>
                </and>
            </expert>
        </search>
    '''
}